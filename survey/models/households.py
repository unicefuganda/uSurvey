import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.datastructures import SortedDict
from model_utils.managers import InheritanceManager
from rapidsms.contrib.locations.models import Location, LocationType
from django.conf import settings
from django.core.paginator import Paginator

from survey.investigator_configs import LEVEL_OF_EDUCATION, MONTHS
from survey.models.base import BaseModel
from survey.models.batch import Batch
from survey.models.investigator import Investigator
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition


class Household(BaseModel):
    investigator = models.ForeignKey(Investigator, null=True, related_name="households")
    ea = models.ForeignKey("EnumerationArea", null=True, related_name="household_enumeration_area")
    uid = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Household Unique Identification")
    random_sample_number = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Household Random Sample Number")
    survey = models.ForeignKey("Survey", null=True, related_name="survey_household")
    household_code = models.CharField(max_length=100, null=True, verbose_name="Household Code")

    MEMBERS_PER_PAGE = 4
    PREVIOUS_PAGE_TEXT = "%s: Back" % getattr(settings, 'USSD_PAGINATION', None).get('PREVIOUS')
    NEXT_PAGE_TEXT = "%s: Next" % getattr(settings, 'USSD_PAGINATION', None).get('NEXT')

    class Meta:
        app_label = 'survey'

    def get_head(self):
        household_head = None
        try:
            household_head = HouseholdHead.objects.get(household=self)
        except:
            pass
        return household_head

    def last_question_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer.exists(): answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def has_next_question(self, batch):
        for household_member in self.household_member.all():
            if not household_member.has_completed(batch):
                return True
        return False

    def has_pending_survey(self):
        for household_member in self.household_member.all():
            if household_member.pending_surveys():
                return True
        return False

    def survey_completed(self):
        batches = self.investigator.get_open_batch()
        for batch in batches:
            if self.has_next_question(batch):
                return False
        return True

    def retake_latest_batch(self):
        batches = self.investigator.get_open_batch()
        from survey.models import Question
        questions = Question.objects.filter(batches__in=batches)
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            getattr(self, related_name).filter(question__in=questions).delete()

    def has_completed_batch(self, batch):
        for member in self.household_member.all():
            if not member.completed_member_batches.filter(batch=batch):
                return False
        return True

    def has_completed_batches(self, batches):
        return self.completed_batches.filter(batch__in=batches).count() == len(batches)

    def batch_completed(self, batch):
        if batch:
            self.batch_completion_batches.get_or_create(household=self, investigator=self.investigator, batch=batch)

    def batch_reopen(self, batch):
        self.completed_batches.filter(household=self).delete()

    def can_retake_survey(self, batch, minutes):
        all_members = self.household_member.all()
        for member in all_members:
            if member.can_retake_survey(batch, minutes):
                return True
        return False

    def _get_related_location_name(self, key, location_hierarchy):
        location_object = location_hierarchy.get(key, None)
        location_name = ""
        if location_object:
            location_name = location_object.name
        return location_name

    def location_hierarchy(self):
        hierarchy = []
        location = self.location
        if location:
            hierarchy.append([location.type.name, location])
            while location.tree_parent:
                location = location.tree_parent
                hierarchy.append([location.type.name, location])
        hierarchy.reverse()
        return SortedDict(hierarchy)

    def get_related_location(self):
        location_hierarchy = self.location_hierarchy()
        keys = ['District', 'County', 'Subcounty', 'Parish', 'Village']
        related_location = SortedDict()
        for key in keys:
            related_location[key] = self._get_related_location_name(key, location_hierarchy)

        return related_location

    def all_members(self):
        household_members = list(self.household_member.order_by('surname').filter(householdhead=None))
        if self.get_head():
            household_members.insert(0, self.get_head())
        return household_members

    def completed_currently_open_batches(self):
        all_members = self.household_member.all().select_subclasses()
        for member in all_members:
            if not member.survey_completed():
                return False
        return True

    def members_list(self, page=1, reporting_non_response=False):
        all_members = self.all_members()
        if reporting_non_response:
            all_members = self.get_non_complete_members()
        paginator = Paginator(all_members, self.MEMBERS_PER_PAGE)
        page = 1 if paginator.num_pages < page else page
        members = paginator.page(page)
        members_list = []

        for member in members:
            name = member.name_used_in_ussd()
            text = "%s: %s" % (all_members.index(member) + 1, name)
            if member.has_completed_survey_options(reporting_non_response):
                text += "*"
            members_list.append(text)
        if members.has_previous():
            members_list.append(self.PREVIOUS_PAGE_TEXT)
        if members.has_next():
            members_list.append(self.NEXT_PAGE_TEXT)
        return "\n".join(members_list)

    def mark_past_answers_as_old(self):
        for member in self.household_member.all():
            member.mark_past_answers_as_old()

    def members_interviewed(self,batch):
        if batch.questions.all().exists():
            return [completed_batch.householdmember for completed_batch in self.completed_batches.filter(batch=batch).exclude(householdmember=None)]
        return []

    def has_members(self):
        return self.household_member.all().count() > 0

    def date_interviewed_for(self, batch):
        if self.has_completed_batch(batch) and self.has_members():
            return self.completed_batches.latest('created').created.strftime('%d-%b-%Y %H:%M:%S')
        return None

    def members_belonging_to_group(self, member_group):
        members_in_group = []
        for member in self.all_members():
            if member.belongs_to(member_group):
                members_in_group.append(member)
        return members_in_group

    def has_answered_non_response(self):
        open_batch = Batch.currently_open_for(self.location)
        has_answered_non_response = self.multichoiceanswer.filter(question__group__name="NON_RESPONSE",
                                                                  batch=open_batch, householdmember=None)
        return has_answered_non_response.exists()

    def has_completed_option_given_(self, registered, non_response_reporting):
        return (registered and self.completed_currently_open_batches()) or\
                    (non_response_reporting and self.has_answered_non_response())

    def get_non_complete_members(self):
        all_completed_members = self.completed_batches.all().values_list('householdmember', flat=True)
        all_household_members = self.all_members()
        non_completed_members = filter(lambda member: member.id not in all_completed_members, all_household_members)
        return non_completed_members

    def has_some_members_who_completed(self):
        return len(self.get_non_complete_members()) > 0 and len(self.get_non_complete_members()) != len(self.all_members())

    def all_members_non_completed(self):
        return len(self.get_non_complete_members()) == len(self.all_members())

    def members_have_completed_non_response(self, batch):
        non_complete_members = self.get_non_complete_members()
        members_completed_non_response = self.multichoiceanswer.filter(question__group__name="NON_RESPONSE", batch=batch)
        return len(non_complete_members) == members_completed_non_response.count()

    @classmethod
    def set_related_locations(cls, households):
        for household in households:
            household.related_locations = household.get_related_location()
        return households

    @classmethod
    def next_uid(cls, survey=None):
        all_households = Household.objects.filter(survey=survey) if survey else Household.objects.filter()
        return (all_households.order_by('uid').reverse()[0].uid + 1) if all_households else 1

    @classmethod
    def all_households_in(cls, location, survey, ea=None):
        all_households = Household.objects.filter(survey=survey)
        if ea:
            return all_households.filter(ea=ea)
        return all_households.filter(ea__locations__in=location.get_descendants(include_self=True))

    @property
    def location(self):
        ea_locations = self.ea.locations.all()[:1]
        return None if not ea_locations.exists() else ea_locations[0]


class HouseholdMember(BaseModel):
    objects = InheritanceManager()

    surname = models.CharField(max_length=25, verbose_name="Family Name")
    first_name = models.CharField(max_length=25, blank=True, null=True, verbose_name="Other Names")
    male = models.BooleanField(default=True, verbose_name="Sex")
    date_of_birth = models.DateField(auto_now=False)
    household = models.ForeignKey(Household, related_name='household_member')

    def is_head(self):
        return False

    def get_head(self):
        self.household.get_head()

    def get_member(self):
        return self

    def name_used_in_ussd(self):
        return self.surname

    def cast_original_type(self):
        head_object = HouseholdHead.objects.filter(householdmember_ptr_id=self.id)
        return head_object[0] if head_object.exists() else self

    def get_location(self):
        return self.household.location

    def attribute_matches(self, condition):
        attributes = {'AGE': self.get_age(),
                      'GENDER': self.male,
                      'GENERAL': self.is_head()
                      }
        return condition.matches(attributes)

    def belongs_to(self, member_group):
        for condition in member_group.get_all_conditions():
            if not self.attribute_matches(condition):
                return False
        return True

    def get_member_groups(self, order_above=0):
        order_above = order_above or 0
        all_groups = HouseholdMemberGroup.objects.select_related('conditions').filter(order__gte=order_above).order_by('order')
        return [group for group in all_groups if self.belongs_to(group)]

    def get_age(self):
        days_in_year = 365.2425
        return int((datetime.date.today() - self.date_of_birth).days / days_in_year)

    def get_dob_attribute(self, type_):
        unknown_attribute = self.unknown_dob_attribute.filter(type=type_)
        if unknown_attribute.exists():
            return 99
        return getattr(self.date_of_birth, type_.lower())

    def get_year_of_birth(self):
        return self.get_dob_attribute('YEAR')

    def get_month_of_birth(self):
        return self.get_dob_attribute('MONTH')

    def get_next_batch(self):
        open_ordered_batches = Batch.open_ordered_batches(self.get_location())

        for batch in open_ordered_batches:
            if batch.has_unanswered_question(self) and not self.completed_member_batches.filter(batch=batch):
                return batch
        return None

    def all_questions_answered(self, all_group_open_questions, batch):
        for question in all_group_open_questions:
            if question.answer_class().objects.filter(question=question, batch=batch,
                                                      householdmember=self).count() == 0:
                return False
        return True

    def last_question_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer.exists() and answer.filter(is_old=False).exists(): answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def has_answered(self, question, batch):
        answer_class = question.answer_class()
        return answer_class.objects.filter(question=question, householdmember=self, batch=batch, is_old=False).count()

    def next_unanswered_question_in(self, member_group, batch, order):
        all_questions = []
        for question in batch.all_questions():
            if (question.question_batch_order.filter(batch=batch)[0].order > order) and (question.group == member_group):
                all_questions.append(question)

        for question in all_questions:
            if not self.has_answered(question, batch):
                return question
        return None

    def next_question(self, question, batch):
        member = self.get_member()
        answer = question.answer_class().objects.select_related('rule').get(householdmember=member, question=question, batch=batch, is_old=False)
        try:
            return question.get_next_question_by_rule(answer, self.household.investigator)
        except ObjectDoesNotExist, e:
            return self.next_question_in_order(batch, question)

    def get_next_question_orders(self, last_question_answered, batch=None):
        group_order = 0
        question_order = 0
        if not last_question_answered:
            last_question_answered = self.last_question_answered()

        if last_question_answered:
            if last_question_answered.subquestion:
                last_question_answered = last_question_answered.parent

            if last_question_answered.is_last_question_of_group(batch):
                group_order = last_question_answered.group.order + 1
            else:
                if batch:
                    batch_question_order_filter = last_question_answered.question_batch_order.all().filter(batch=batch)
                    question_order = batch_question_order_filter[0].order if batch_question_order_filter else 0
                else:
                    question_order = last_question_answered.order
                group_order = last_question_answered.group.order

        return group_order, question_order

    def next_question_in_order(self, batch, last_question_answered=None):
        group_order, question_order = self.get_next_question_orders(last_question_answered, batch)

        for member_group in self.get_member_groups(order_above=group_order):
            next_group_question = self.next_unanswered_question_in(member_group, batch, question_order)
            if next_group_question:
                return next_group_question
        return None

    def can_retake_survey(self, batch=None, minutes=0):
        if not batch:
            last_batch_completed_by_member = self.completed_member_batches.filter(householdmember=self,
                                                                              household=self.household).order_by('created').reverse()
        else:
            last_batch_completed_by_member = self.completed_member_batches.filter(batch=batch, householdmember=self,
                                                                              household=self.household).order_by('created').reverse()

        if last_batch_completed_by_member:
            last_batch_completed_time = last_batch_completed_by_member[0].created

            elapsed_seconds = (datetime.datetime.utcnow().replace(
                tzinfo=last_batch_completed_time.tzinfo) - last_batch_completed_time).seconds
            expected_timeout = minutes * 60

            if expected_timeout >= elapsed_seconds:
                return True
            return False
        return True

    def location(self):
        return self.household.location

    def batch_completed(self, batch):
        return self.completed_member_batches.get_or_create(householdmember=self, household=self.household,
                                                           investigator=self.household.investigator, batch=batch)

    def survey_completed(self):
        return self.get_next_batch() is None

    def has_started_the_survey(self):
        return bool(self.last_question_answered())

    def pending_surveys(self):
        return not (bool(self.survey_completed()) and bool(self.has_started_the_survey()))

    def has_open_batches(self):
        for batch in self.household.investigator.get_open_batch():
            if not self.completed_member_batches.filter(householdmember=self, household=self.household,
                                                        investigator=self.household.investigator, batch=batch):
                return True
        return False

    def has_completed(self, batch):
        for question in batch.all_questions():
            if not self.has_answered(question, batch):
                return False
        return True

    def mark_past_answers_as_old(self):
        self.completed_member_batches.all().delete()
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            getattr(self, related_name).all().update(is_old=True)

    def answers_for(self, questions, general_group):
        answers = []
        for question in questions:
            answer_class = question.answer_class()
            answer = answer_class.objects.filter(question=question, household=self.household)
            answer = self._filter_answer(answer, question, general_group)
            answers.extend(self._format_answer(answer, question))
        return answers

    @classmethod
    def _format_answer(cls, answer, question):
        if answer:
            answer = answer[0]
            if question.is_multichoice():
                option = answer.answer
                return [option.order, option.text]
            return [answer.answer]
        return ['']

    def _filter_answer(self, answer, question, general_group):
        if question.belongs_to(general_group):
            return answer.filter(householdmember=self.get_head())
        return answer.filter(householdmember=self)

    def has_completed_survey_options(self, reporting_non_response):
        return (self.survey_completed() and not reporting_non_response)\
            or (reporting_non_response and self.has_answered_non_response())

    def has_answered_non_response(self):
        open_batch = Batch.currently_open_for(self.household.location)
        return self.multichoiceanswer.filter(question__group__name="NON_RESPONSE", batch=open_batch).count() > 0

    @staticmethod
    def belongs_to_general_group(question):
        return question.group.name == GroupCondition.GROUP_TYPES['GENERAL']

    class Meta:
        app_label = 'survey'
        get_latest_by = 'created'


class HouseholdHead(HouseholdMember):
    occupation = models.CharField(max_length=100, blank=False, null=False,
                                  verbose_name="Occupation / Main Livelihood", default="16")
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    resident_since_year = models.PositiveIntegerField(validators=[MinValueValidator(1930), MaxValueValidator(2100)],
                                                      null=False, default=1984)
    resident_since_month = models.PositiveIntegerField(null=False, choices=MONTHS, blank=False, default=5)

    class Meta:
        app_label = 'survey'

    def is_head(self):
        return True

    def get_head(self):
        return self

    def get_member(self):
        return HouseholdMember.objects.get(householdhead=self)

    def name_used_in_ussd(self):
        return self.surname + " - (respondent)"


