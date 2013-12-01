import datetime
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.datastructures import SortedDict
from rapidsms.contrib.locations.models import Location, LocationType
from rapidsms.router import send
from survey.investigator_configs import LEVEL_OF_EDUCATION, LANGUAGES, COUNTRY_PHONE_CODE
from survey.models.backend import Backend
from survey.models.base import BaseModel
from survey.models.batch import Batch, BatchLocationStatus


class Investigator(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    mobile_number = models.CharField(validators=[MinLengthValidator(9), MaxLengthValidator(9)], max_length=10,
                                     unique=True, null=False, blank=False)
    male = models.BooleanField(default=True, verbose_name="Sex")
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(50)], null=True)
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    location = models.ForeignKey(Location, null=True)
    language = models.CharField(max_length=100, null=True, choices=LANGUAGES,
                                blank=False, default='English', verbose_name="Preferred language of communication")
    backend = models.ForeignKey(Backend, null=True, verbose_name="Connection")
    weights = models.FloatField(default=0, blank=False)
    is_blocked = models.BooleanField(default=False)

    HOUSEHOLDS_PER_PAGE = 4
    PREVIOUS_PAGE_TEXT = "%s: Back" % getattr(settings, 'USSD_PAGINATION', None).get('PREVIOUS')
    NEXT_PAGE_TEXT = "%s: Next" % getattr(settings, 'USSD_PAGINATION', None).get('NEXT')

    DEFAULT_CACHED_VALUES = {
        'REANSWER': [],
        'INVALID_ANSWER': [],
        'CONFIRM_END_INTERVIEW': [],
        'IS_REGISTERING_HOUSEHOLD': None,
        'IS_REPORTING_NON_RESPONSE': False,
        'registration_dict': {},
        'is_head': None,
        'is_selecting_member': False
    }

    def __init__(self, *args, **kwargs):
        super(Investigator, self).__init__(*args, **kwargs)
        self.identity = COUNTRY_PHONE_CODE + self.mobile_number
        self.cache_key = "Investigator-%s" % self.pk
        self.generate_cache()

    class Meta:
        app_label = 'survey'

    def has_households(self, survey=None):
        all_households = self.households.all()
        survey_households = all_households.filter(survey=survey) if survey else all_households
        return survey_households.count() > 0

    def generate_cache(self):
        if not cache.get(self.cache_key):
            cache.set(self.cache_key, self.DEFAULT_CACHED_VALUES)

    def set_in_cache(self, key, value):
        cached = cache.get(self.cache_key)
        cached[key] = value
        cache.set(self.cache_key, cached)

    def get_from_cache(self, key):
        return cache.get(self.cache_key)[key]

    def clear_interview_caches(self):
        cache.delete(self.cache_key)

    def clear_all_cache_fields_except(self, field_name):
        old_field_value = self.get_from_cache(field_name)
        cache.delete(self.cache_key)
        self.generate_cache()
        self.set_in_cache(field_name, old_field_value)

    def last_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer: answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0]

    def last_registered(self):
        members = []
        for household in self.households.all():
            all_members = household.household_member.all()
            if all_members: members.append(all_members.latest())
        if members:
            return sorted(members, key=lambda x: x.created, reverse=True)[0]

    def last_answered_question(self):
        return self.last_answered().question

    def member_answered(self, question, household_member, answer, batch):
        answer_class = question.answer_class()
        if question.is_multichoice():
            answer = question.get_option(answer, self)
            if not answer:
                return question

        answer = answer_class.objects.create(investigator=self, question=question, householdmember=household_member,
                                             answer=answer, household=household_member.household, batch=batch)
        if answer.pk:
            next_question = household_member.next_question(question, batch)
            if next_question is None:
                household_member.batch_completed(batch)
                next_batch = household_member.get_next_batch()
                next_question = household_member.next_question_in_order(next_batch) if next_batch else None
            return next_question

        return question

    def last_answer_for(self, question):
        answer_class = question.answer_class()
        return answer_class.objects.filter(investigator=self, question=question).latest()

    def reanswer(self, question):
        self.add_ussd_variable('REANSWER', question)
        self.last_answer_for(question).delete()

    def invalid_answer(self, question):
        self.add_ussd_variable('INVALID_ANSWER', question)

    def can_end_the_interview(self, question):
        return question in self.get_from_cache('CONFIRM_END_INTERVIEW')

    def confirm_end_interview(self, question):
        self.add_ussd_variable("CONFIRM_END_INTERVIEW", question)

    def add_ussd_variable(self, label, question):
        questions = self.get_from_cache(label)
        questions.append(question)
        self.set_in_cache(label, questions)

    def remove_ussd_variable(self, label, question):
        questions = self.get_from_cache(label)
        if question in questions:
            questions.remove(question)
            self.set_in_cache(label, questions)

    def filter_non_completed_households(self, all_households):
        all_completed_households = self.batch_completion_completed_households.all().values_list('household', flat=True)
        non_completed_households = filter(lambda household: household.id not in all_completed_households, all_households)
        return non_completed_households

    def households_list(self, page=1, registered=False, open_survey=None, non_response_reporting=False):
        all_households = list(self.all_households(open_survey, non_response_reporting))
        paginator = Paginator(all_households, self.HOUSEHOLDS_PER_PAGE)
        households = paginator.page(page)
        households_list = []
        for household in households:
            household_head = household.get_head()
            text = "%s: Household-%s" % (all_households.index(household) + 1,  household.random_sample_number)
            text = "%s-%s"%(text, household_head.surname) if household_head else text
            if household.has_completed_option_given_(registered, non_response_reporting):
                text += "*"
            households_list.append(text)
        if households.has_previous():
            households_list.append(self.PREVIOUS_PAGE_TEXT)
        if households.has_next():
            households_list.append(self.NEXT_PAGE_TEXT)
        return "\n".join(households_list)

    def all_households(self, open_survey=None, non_response_reporting=False):
        all_households = self.households.order_by('created').all()
        all_households = all_households.filter(survey=open_survey) if open_survey else all_households
        if non_response_reporting:
            all_households = self.filter_non_completed_households(all_households)
        return all_households

    def completed_non_response_reporting(self, open_survey=None):
        all_households = self.all_households(open_survey=open_survey, non_response_reporting=True)
        # map(lambda household: group_choices.append((group.id, group.name)), HouseholdMemberGroup.objects.all().exclude(name='REGISTRATION GROUP'))
        for household in all_households:
            if not household.has_answered_non_response():
                return False
        return True

    def completed_open_surveys(self, open_survey=None):
        for household in self.all_households(open_survey):
            if not household.completed_currently_open_batches():
                return False
        return True

    def get_open_batch(self):
        batch_locations = self.location.open_batches.all()
        batches = [batch_location.batch for batch_location in batch_locations]
        return batches

    def first_open_batch(self):
        open_batches = self.get_open_batch()
        query_open_batches = Batch.objects.filter(id__in=[batch.id for batch in open_batches])
        batch = query_open_batches.order_by('order')[0]
        return batch

    def has_open_batch(self):
        locations = self.location.get_ancestors(include_self=True)
        return BatchLocationStatus.objects.filter(location__in=locations).count() > 0

    def created_member_within(self, minutes, open_survey=None):
        last_member = self.last_registered()
        if not last_member:
            return False
        if last_member.household.survey != open_survey:
            return False
        last_active = last_member.created
        timeout = datetime.datetime.utcnow().replace(tzinfo=last_active.tzinfo) - datetime.timedelta(minutes=minutes)
        return last_active >= timeout

    def was_active_within(self, minutes):
        last_answered = self.last_answered()
        if not last_answered:
            return False
        last_active = last_answered.created
        timeout = datetime.datetime.utcnow().replace(tzinfo=last_active.tzinfo) - datetime.timedelta(minutes=minutes)
        return last_active >= timeout

    def location_hierarchy(self):
        hierarchy = []
        location = self.location
        hierarchy.append([location.type.name, location])
        while location.tree_parent:
            location = location.tree_parent
            hierarchy.append([location.type.name, location])
        hierarchy.reverse()
        return SortedDict(hierarchy)

    def locations_in_hierarchy(self):
        hierarchy = []
        location = self.location
        hierarchy.append(location)
        while location.tree_parent:
            location = location.tree_parent
            hierarchy.append(location)
        hierarchy.reverse()
        return hierarchy

    def remove_invalid_households(self):
        all_households = self.households.all()
        for household in all_households:
            if household.location != self.location:
                self.households.remove(household)

    def get_open_batch_for_survey(self,survey):
        batches = self.get_open_batch()
        return[batch for batch in batches if batch.survey == survey]

    def completed_survey(self,survey):
        if self.get_open_batch_for_survey(survey):
            for household in self.all_households():
                if not household.survey_completed():
                    return False
            return True
        return False

    def get_household_code(self):
        household_code = ""
        location_hierarchy = self.locations_in_hierarchy()
        for location in location_hierarchy:
            all_locations = location.code.all()

            location_code = all_locations[0] if all_locations else None
            if location_code:
                household_code += location_code.code
        return household_code

    def can_report_non_response(self):
        return BatchLocationStatus.objects.filter(location=self.location, non_response=True).count() > 0


    @classmethod
    def get_summarised_answers_for(self, questions, data):
        for investigator in self.objects.all():
            for household in investigator.households.all():
                for member in household.all_members():
                    member_gender = 'Male' if member.male else "Female"
                    household_location = household.location
                    household_locations = household_location.get_ancestors(include_self=True)
                    answers = []
                    for location in household_locations:
                        answers.append(location.name)

                    answers = answers + [household.household_code, member.surname, str(int(member.get_age())),
                                         str(member.get_month_of_birth()), str(member.get_year_of_birth()),
                                         member_gender]
                    answers = answers + member.answers_for(questions)
                    data.append(answers)

    @classmethod
    def sms_investigators_in_locations(cls, locations, text):
        investigators = []
        for location in locations:
            investigators.extend(Investigator.lives_under_location(location))
        send(text, investigators)

    @classmethod
    def lives_under_location(cls, location):
        locations = location.get_descendants(include_self=True)
        return Investigator.objects.filter(location__in=locations)

    @classmethod
    def genrate_completion_report(cls, survey):
        header = ['Investigator', 'Phone Number']
        header.extend([loc.name for loc in LocationType.objects.all()])
        data = [header]
        for investigator in Investigator.objects.all():
            if investigator.completed_survey(survey):
                row=[investigator.name,investigator.mobile_number]
                if investigator.location:
                    row.extend([loc.name for loc in investigator.location_hierarchy().values()])
                data.append(row)
        return data
