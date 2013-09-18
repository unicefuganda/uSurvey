import datetime
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.datastructures import SortedDict
from rapidsms.contrib.locations.models import Location
from rapidsms.router import send
from survey.investigator_configs import LEVEL_OF_EDUCATION, LANGUAGES, COUNTRY_PHONE_CODE
from survey.models.backend import Backend
from survey.models.base import BaseModel
from survey.models.batch import Batch, BatchLocationStatus


class Investigator(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    mobile_number = models.CharField(validators=[MinLengthValidator(9), MaxLengthValidator(9)], max_length=10, unique=True, null=False, blank=False)
    male = models.BooleanField(default=True, verbose_name="Sex")
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(50)], null=True)
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary', verbose_name="Highest level of education completed")
    location = models.ForeignKey(Location, null=True)
    language = models.CharField(max_length=100, null=True, choices=LANGUAGES,
                                blank=False, default='English', verbose_name="Preferred language of communication")
    backend = models.ForeignKey(Backend, null=True, verbose_name="Connection")
    weights = models.FloatField(default=0, blank=False)

    HOUSEHOLDS_PER_PAGE = 4
    PREVIOUS_PAGE_TEXT = "%s: Back" % getattr(settings,'USSD_PAGINATION',None).get('PREVIOUS')
    NEXT_PAGE_TEXT = "%s: Next" % getattr(settings,'USSD_PAGINATION',None).get('NEXT')

    DEFAULT_CACHED_VALUES = {
        'REANSWER': [],
        'INVALID_ANSWER': [],
        'CONFIRM_END_INTERVIEW': [],
    }

    def __init__(self, *args, **kwargs):
        super(Investigator, self).__init__(*args, **kwargs)
        self.identity = COUNTRY_PHONE_CODE + self.mobile_number
        self.cache_key = "Investigator-%s" % self.pk
        self.generate_cache()

    class Meta:
        app_label = 'survey'


    def has_households(self):
        return self.households.count() > 0

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

    def next_answerable_question(self, household_member):
        return household_member.next_question()

    def last_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer:answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0]

    def last_answered_question(self):
        return self.last_answered().question

    def answered(self, question, household, answer):
        answer_class = question.answer_class()
        if question.is_multichoice():
            answer = question.get_option(answer, self)
            if not answer:
                return question
        if answer_class.objects.create(investigator=self, question=question, household=household, answer=answer).pk:
            next_question = household.next_question(last_question_answered = question)
            if next_question == None or next_question.batch != question.batch:
                household.batch_completed(question.batch)
            return next_question
        else:
            return question

    def member_answered(self, question, household_member, answer):
        answer_class = question.answer_class()
        if question.is_multichoice():
            answer = question.get_option(answer, self)
            if not answer:
                return question

        answer = answer_class.objects.create(investigator=self, question=question, householdmember=household_member,
                                             answer=answer, household=household_member.household)
        if answer.pk:
            next_question = question.next_question_for_household_member(household_member)

            if next_question == None or next_question.batch != question.batch:
                household_member.batch_completed(question.batch)
            return next_question
        else:
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

    def households_list(self, page=1):
        all_households = list(self.all_households())
        paginator = Paginator(all_households, self.HOUSEHOLDS_PER_PAGE)
        households = paginator.page(page)
        households_list = []
        open_batches = self.get_open_batch()
        for household in households:
            text = "%s: %s" % (all_households.index(household) + 1, household.get_head().surname)
            if household.has_completed_batches(open_batches):
                text += "*"
            households_list.append(text)
        if households.has_previous():
            households_list.append(self.PREVIOUS_PAGE_TEXT)
        if households.has_next():
            households_list.append(self.NEXT_PAGE_TEXT)
        return "\n".join(households_list)

    def all_households(self):
        return self.households.order_by('created').all()

    def completed_open_surveys(self):
        for household in self.all_households():
            if household.has_pending_survey():
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

    def was_active_within(self, minutes):
        last_answered = self.last_answered()
        if not last_answered:
            return False
        last_active = last_answered.created
        timeout = datetime.datetime.utcnow().replace(tzinfo=last_active.tzinfo) - datetime.timedelta(minutes=minutes)
        return last_active >= timeout

    def pending_households_for(self, batch):
        completed = batch.completed_households.filter(investigator=self).count()
        return self.households.count() - completed

    def location_hierarchy(self):
        hierarchy = []
        location = self.location
        hierarchy.append([location.type.name, location])
        while location.tree_parent:
            location = location.tree_parent
            hierarchy.append([location.type.name, location])
        hierarchy.reverse()
        return SortedDict(hierarchy)

    @classmethod
    def get_summarised_answers_for(self, batch, questions, data):
        for investigator in self.objects.all():
            for household in investigator.households.all():
                answers = [investigator.location.name, household.get_head().surname]
                answers = answers + household.answers_for(questions)
                data.append(answers)

    @classmethod
    def sms_investigators_in_locations(self, locations, text):
        investigators = []
        for location in locations:
            investigators.extend(Investigator.lives_under_location(location))
        send(text, investigators)

    @classmethod
    def lives_under_location(self, location):
        locations = location.get_descendants(include_self=True)
        return Investigator.objects.filter(location__in=locations)