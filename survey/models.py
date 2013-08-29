from django.db import models
from django.core.validators import *
from django_extensions.db.models import TimeStampedModel
from rapidsms.contrib.locations.models import Location
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from survey.investigator_configs import *
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.conf import settings
from django.core.cache import cache
import datetime
from django.db.models import Count
from django.conf import settings
from rapidsms.router import send
import random
from django.utils.datastructures import SortedDict
from django.contrib.auth.models import User
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.db.models import Max


class BaseModel(TimeStampedModel):
    class Meta:
        app_label = 'survey'
        abstract = True


class UserProfile(BaseModel):
    user = models.OneToOneField(User, related_name="userprofile")
    mobile_number = models.CharField(validators=[MinLengthValidator(9), MaxLengthValidator(9)], max_length=10, unique=True, null=False, blank=False)


class Backend(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return self.name


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

    def next_answerable_question(self, household):
        return household.next_question()

    def last_answered(self):
        answered = []
        for klass in [NumericalAnswer, TextAnswer, MultiChoiceAnswer]:
            try:
                answer = klass.objects.filter(investigator=self).latest()
                if answer:answered.append(answer)
            except ObjectDoesNotExist, e:
                pass
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0]

    def last_answered_question(self):
        self.last_answered().question

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
            text = "%s: %s" % (all_households.index(household) + 1, household.head.surname)
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
            if household.next_question():
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
                answers = [investigator.location.name, household.head.surname]
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


class LocationAutoComplete(models.Model):
    location = models.ForeignKey(Location, null=True)
    text = models.CharField(max_length=500)

    class Meta:
        app_label = 'survey'


class Household(BaseModel):
    investigator = models.ForeignKey(Investigator, null=True, related_name="households")
    number_of_males = models.PositiveIntegerField(blank=False, default=0,
                        verbose_name="How many males reside in this household?")
    number_of_females = models.PositiveIntegerField(blank=False, default=0,
                        verbose_name="How many females reside in this household?")

    def last_question_answered(self):
        answered = []
        for klass in [NumericalAnswer, TextAnswer, MultiChoiceAnswer]:
            try:
                answer = klass.objects.filter(household=self).latest()
                if answer: answered.append(answer)
            except ObjectDoesNotExist, e:
                pass
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def next_question(self, last_question_answered=None):
        if not last_question_answered:
            last_question_answered = self.last_question_answered()

        investigator_location = self.investigator.location

        if not last_question_answered or not last_question_answered.is_in_open_batch(investigator_location):
            open_batch = Batch.currently_open_for(location=investigator_location)
            if open_batch:
                question = open_batch.first_question()
                return question
        else:
            return last_question_answered.next_question_for_household(self)

    def has_pending_survey(self):
        last_answered_question = self.last_question_answered()
        if not last_answered_question or not last_answered_question.next_question_for_household(self):
            return False
        else:
            return True

    def survey_completed(self):
        return not self.next_question()

    def retake_latest_batch(self):
        batches = self.investigator.get_open_batch()
        for batch in batches:
            questions = batch.all_questions()
            for klass in [NumericalAnswer, TextAnswer, MultiChoiceAnswer]:
                klass.objects.filter(question__in=questions, household=self).delete()

    def has_completed_batch(self, batch):
        return self.completed_batches.filter(batch=batch).count() > 0

    def has_completed_batches(self, batches):
        return self.completed_batches.filter(batch__in=batches).count() == len(batches)

    def batch_completed(self, batch):
        return self.completed_batches.get_or_create(household=self, investigator=self.investigator, batch=batch)

    def batch_reopen(self, batch):
        self.completed_batches.filter(household=self).delete()

    def can_retake_survey(self, batch, minutes):
        last_batch_completed_time = self.completed_batches.filter(batch=batch, household=self)[0].created
        timeout = datetime.datetime.utcnow().replace(tzinfo=last_batch_completed_time.tzinfo) - datetime.timedelta(minutes=minutes)
        return last_batch_completed_time >= timeout

    def answers_for(self, questions):
        answers = []
        for question in questions:
            answer_class = question.answer_class()
            answer = answer_class.objects.filter(question=question, household=self)
            if answer:
                answer = answer[0]
                if question.is_multichoice():
                    option = answer.answer
                    answers.append(option.order)
                    answers.append(option.text)
                else:
                    answers.append(answer.answer)
            else:
                answers.append('')
        return answers

    def _get_related_location_name(self, key, location_hierarchy):
        location_object = location_hierarchy.get(key, None)

        location_name = ""

        if location_object:
            location_name = location_object.name

        return location_name

    def get_related_location(self):
        location_hierarchy = self.investigator.location_hierarchy()

        keys = ['District', 'County', 'Subcounty', 'Parish', 'Village']
        related_location = {}
        for key in keys:
            related_location[key] = self._get_related_location_name(key, location_hierarchy)

        return related_location

    @classmethod
    def set_related_locations(cls, households):
        for household in households:
            household.related_locations = household.get_related_location()
        return households


class HouseholdHead(BaseModel):
    household = models.OneToOneField(Household, null=True, related_name="head")
    surname = models.CharField(max_length=12, blank=False, null=True, verbose_name="Family Name")
    first_name = models.CharField(max_length=12, blank=False, null=True, verbose_name="Other Names")
    age = models.PositiveIntegerField(validators=[MinValueValidator(10), MaxValueValidator(99)], null=True)
    male = models.BooleanField(default=True, verbose_name="Gender")
    occupation = models.CharField(max_length=100, blank=False, null=False,
                                   verbose_name="Occupation / Main Livelihood", default="16")
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary', verbose_name="Highest level of education completed")
    resident_since_year = models.PositiveIntegerField(validators=[MinValueValidator(1930), MaxValueValidator(2100)],
                                                         null=False, default=1984)
    resident_since_month = models.PositiveIntegerField(null=False, choices=MONTHS, blank=False, default=5)


class Children(BaseModel):
    household = models.OneToOneField(Household, null=True, related_name="children")
    aged_between_5_12_years = models.PositiveIntegerField(blank=False, default=0, verbose_name="How many children are aged 5-12 years?")
    aged_between_13_17_years = models.PositiveIntegerField(blank=False, default=0, verbose_name="13-17 years?")
    aged_between_0_5_months = models.PositiveIntegerField(blank=False, default=0, verbose_name="How many of these children are aged 0-5 months?")
    aged_between_6_11_months = models.PositiveIntegerField(blank=False, default=0, verbose_name="6-11 months?")
    aged_between_12_23_months = models.PositiveIntegerField(blank=False, default=0, verbose_name="12-23 months?")
    aged_between_24_59_months = models.PositiveIntegerField(blank=False, default=0, verbose_name="24-59 months?")


class Women(BaseModel):
   household = models.OneToOneField(Household, null=True, related_name="women")
   aged_between_15_19_years = models.PositiveIntegerField(blank=False, default=0, verbose_name="How many of these women are aged 15-19 years?")
   aged_between_20_49_years = models.PositiveIntegerField(blank=False, default=0, verbose_name="20-49 years?")


class Batch(BaseModel):
    order = models.PositiveIntegerField(max_length=2, null=True)
    name = models.CharField(max_length=100, blank=False,null=True)
    description = models.CharField(max_length=300,blank=True,null=True)

    def save(self, *args, **kwargs):
        last_order = Batch.objects.aggregate(Max('order'))['order__max']
        self.order = last_order + 1 if last_order else 1
        super(Batch, self).save(*args, **kwargs)

    @classmethod
    def currently_open_for(self, location):
        locations = location.get_ancestors(include_self=True)
        open_batches = BatchLocationStatus.objects.filter(location__in=locations)
        if open_batches.count() > 0:
            return open_batches.order_by('created').all()[:1].get().batch

    def first_question(self):
        return self.questions.get(order=1)

    def all_questions(self):
        return Question.objects.filter(batch=self)

    def open_for_location(self, location):
        all_related_locations = location.get_descendants(include_self=False).all()
        for related_location in all_related_locations:
            self.open_locations.get_or_create(batch=self, location=related_location)

        return self.open_locations.get_or_create(batch=self, location=location)

    def is_closed_for(self, location):
        return self.open_locations.filter(location=location).count() == 0

    def is_open_for(self, location):
        return not self.is_closed_for(location)

    def close_for_location(self, location):
        self.open_locations.filter(batch=self).delete()

    def get_next_indicator(self, order, location):
        indicator = self.indicators.filter(order = order + 1)
        if indicator:
            return indicator[0]
        else:
            return self.get_indicator_from_next_open_batch(location = location)

    def get_next_open_batch(self, order, location):
        next_batch_in_order = Batch.objects.filter(order__gt = order).order_by('order')

        next_open_batch = location.open_batches.filter(batch__in = next_batch_in_order)
        if next_open_batch:
            return next_open_batch[0].batch

    def generate_report(self):
        data = []
        header = ['Location', 'Household Head Name']
        questions = []
        for question in self.questions.order_by('order').filter(subquestion=False):
            questions.append(question)
            header.append(question.identifier)
            if question.is_multichoice():
                header.append('')
        data = [header]
        Investigator.get_summarised_answers_for(self, questions, data)
        return data

    def get_next_question(self, order, location):
        if self.is_open_for(location=location):
            question = self.questions.filter(order=order + 1)

            if question:
                return question[0]
            else:
                return self.get_question_from_next_batch(location=location)
        else:
            return self.get_question_from_next_batch(location=location)

    def get_question_from_next_batch(self, location):
        next_batch = self.get_next_open_batch(order=self.order, location=location)
        if next_batch:
            return next_batch.get_next_question(order=0, location=location)


class BatchLocationStatus(BaseModel):
    batch = models.ForeignKey(Batch, null=True, related_name="open_locations")
    location = models.ForeignKey(Location, null=True, related_name="open_batches")


class HouseholdBatchCompletion(BaseModel):
    household = models.ForeignKey(Household, null=True, related_name="completed_batches")
    batch = models.ForeignKey(Batch, null=True, related_name="completed_households")
    investigator = models.ForeignKey(Investigator, null=True, related_name="completed_batches")

    @classmethod
    def households_status(self, investigators, batch):
        households = Household.objects.filter(investigator__in = investigators)
        completed = batch.completed_households.filter(household__in = households).count()
        pending = households.count() - completed
        return {'completed': completed, 'pending': pending}

    @classmethod
    def clusters_status(self, investigators, batch):
        completed_clusters = self.objects.values('investigator').annotate(number_of_households=Count('household')).filter(number_of_households = NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR, batch = batch, investigator__in = investigators).count()
        pending_clusters = investigators.count() - completed_clusters
        return {'completed': completed_clusters, 'pending': pending_clusters}

    @classmethod
    def pending_investigators(self, investigators, batch):
        completed_clusters = self.objects.values('investigator').annotate(number_of_households=Count('household')).filter(number_of_households = NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR, batch = batch)
        investigator_ids = completed_clusters.values_list('investigator', flat=True)
        return investigators.exclude(id__in=investigator_ids)


    @classmethod
    def status_of_batch(self, batch, location):
        locations = location.get_descendants(include_self=True) if location else Location.objects.all()
        investigators = Investigator.objects.filter(location__in = locations)
        return self.households_status(investigators, batch), self.clusters_status(investigators, batch), self.pending_investigators(investigators, batch)


class Question(BaseModel):
    NUMBER = 'number'
    TEXT = 'text'
    MULTICHOICE = 'multichoice'
    TYPE_OF_ANSWERS = {
        (NUMBER, 'Number'),
        (TEXT, 'Text'),
        (MULTICHOICE, 'Multichoice')
    }
    TYPE_OF_ANSWERS_CLASS = {
        NUMBER: 'NumericalAnswer',
        TEXT: 'TextAnswer',
        MULTICHOICE: 'MultiChoiceAnswer'
    }

    OPTIONS_PER_PAGE = 3
    PREVIOUS_PAGE_TEXT = "%s: Back" % getattr(settings,'USSD_PAGINATION',None).get('PREVIOUS')
    NEXT_PAGE_TEXT = "%s: Next" % getattr(settings,'USSD_PAGINATION',None).get('NEXT')

    identifier = models.CharField(max_length=100, blank=False, null=True)
    batch = models.ForeignKey(Batch, null=True, related_name="questions")
    text = models.CharField(max_length=150, blank=False, null=False)
    answer_type = models.CharField(max_length=15, blank=False, null=False, choices=TYPE_OF_ANSWERS)
    order = models.PositiveIntegerField(max_length=2, null=True)
    subquestion = models.BooleanField(default=False)
    parent = models.ForeignKey("Question", null=True, related_name="children")

    def get_option(self, answer, investigator):
        try:
            return self.options.get(order=int(answer))
        except (QuestionOption.DoesNotExist, ValueError) as e:
            investigator.invalid_answer(self)
            return False

    def is_multichoice(self):
        return self.answer_type == self.MULTICHOICE

    def answer_class(self):
        return eval(Question.TYPE_OF_ANSWERS_CLASS[self.answer_type])

    def options_in_text(self, page=1):
        paginator = Paginator(self.options.order_by('order').all(), self.OPTIONS_PER_PAGE)
        options = paginator.page(page)
        options_list = [option.to_text() for option in options]
        if options.has_previous():
            options_list.append(self.PREVIOUS_PAGE_TEXT)
        if options.has_next():
            options_list.append(self.NEXT_PAGE_TEXT)
        return "\n".join(options_list)

    def get_next_question_by_rule(self, answer, investigator):
        if self.rule.validate(answer):
            return self.rule.action_to_take(investigator, answer)
        else:
            raise ObjectDoesNotExist

    def next_question_for_household(self, household):
        answer = self.answer_class().objects.get(household=household, question=self)
        try:
            return self.get_next_question_by_rule(answer, household.investigator)
        except ObjectDoesNotExist, e:
            return self.next_question(location=household.investigator.location)

    def next_question(self, location):
        order = self.parent.order if self.subquestion else self.order
        return self.batch.get_next_question(order, location=location)

    def to_ussd(self, page=1):
        if self.answer_type == self.MULTICHOICE:
            text = "%s\n%s" % (self.text, self.options_in_text(page))
            return text
        else:
            return self.text

    def is_in_open_batch(self, location):
        return self.batch.is_open_for(location)


class QuestionOption(BaseModel):
    question = models.ForeignKey(Question, null=True, related_name="options")
    text = models.CharField(max_length=150, blank=False, null=False)
    order = models.PositiveIntegerField(max_length=2, null=True)

    def to_text(self):
        return "%d: %s" % (self.order, self.text)


class Answer(BaseModel):
    investigator = models.ForeignKey(Investigator, null=True)
    household = models.ForeignKey(Household, null=True)
    question = models.ForeignKey(Question, null=True)
    rule_applied = models.ForeignKey("AnswerRule", null=True)

    class Meta:
        app_label = 'survey'
        abstract = True
        get_latest_by = 'created'


class NumericalAnswer(Answer):
    answer = models.PositiveIntegerField(max_length=5, null=True)

    def save(self, *args, **kwargs):
        try:
            self.answer = int(self.answer)
            super(NumericalAnswer, self).save(*args, **kwargs)
        except ValueError, e:
            self.investigator.invalid_answer(self.question)


class TextAnswer(Answer):
    answer = models.CharField(max_length=100, blank=False, null=False)


class MultiChoiceAnswer(Answer):
    answer = models.ForeignKey(QuestionOption, null=True)


class AnswerRule(BaseModel):
    ACTIONS = {
                'END_INTERVIEW': 'END_INTERVIEW',
                'SKIP_TO': 'SKIP_TO',
                'REANSWER': 'REANSWER',
                'ASK_SUBQUESTION': 'ASK_SUBQUESTION',
    }
    ACTION_METHODS = {
                'END_INTERVIEW': 'end_interview',
                'SKIP_TO': 'skip_to',
                'REANSWER': 'reanswer',
                'ASK_SUBQUESTION': 'ask_subquestion',
    }
    CONDITIONS = {
                'EQUALS': 'EQUALS',
                'EQUALS_OPTION': 'EQUALS_OPTION',
                'GREATER_THAN_QUESTION': 'GREATER_THAN_QUESTION',
                'GREATER_THAN_VALUE': 'GREATER_THAN_VALUE',
                'LESS_THAN_QUESTION': 'LESS_THAN_QUESTION',
                'LESS_THAN_VALUE': 'LESS_THAN_VALUE',
    }
    CONDITION_METHODS = {
                'EQUALS': 'is_equal',
                'EQUALS_OPTION': 'equals_option',
                'GREATER_THAN_QUESTION': 'greater_than_question',
                'GREATER_THAN_VALUE': 'greater_than_value',
                'LESS_THAN_QUESTION': 'less_than_question',
                'LESS_THAN_VALUE': 'less_than_value',
    }

    question = models.OneToOneField(Question, null=True, related_name="rule")
    action = models.CharField(max_length=100, blank=False, null=False, choices=ACTIONS.items())
    condition = models.CharField(max_length=100, blank=False, null=False, choices=CONDITIONS.items())
    next_question = models.ForeignKey(Question, null=True, related_name="parent_question_rules")
    validate_with_value = models.PositiveIntegerField(max_length=2, null=True)
    validate_with_question = models.ForeignKey(Question, null=True)
    validate_with_option = models.ForeignKey(QuestionOption, null=True)

    def is_equal(self, answer):
        return self.validate_with_value == answer.answer

    def equals_option(self, answer):
        return self.validate_with_option == answer.answer

    def greater_than_question(self, answer):
        return answer.answer > answer.investigator.last_answer_for(self.validate_with_question).answer

    def greater_than_value(self, answer):
        return answer.answer > self.validate_with_value

    def less_than_question(self, answer):
        return answer.answer < answer.investigator.last_answer_for(self.validate_with_question).answer

    def less_than_value(self, answer):
        return answer.answer < self.validate_with_value

    def end_interview(self, investigator, answer):
        if answer.rule_applied:
            return None
        if not investigator.can_end_the_interview(self.question):
            investigator.confirm_end_interview(self.question)
            return self.reanswer(investigator, answer)
        else:
            self.rule_applied_to(answer)
            return None

    def rule_applied_to(self, answer):
        answer.rule_applied = self
        answer.save()

    def skip_to(self, investigator, answer):
        return self.next_question

    def reanswer(self, investigator, answer):
        investigator.reanswer(self.question)
        if self.validate_with_question:
            investigator.reanswer(self.validate_with_question)
            return self.validate_with_question
        else:
            return self.question

    def ask_subquestion(self, investigator, answer):
        return self.skip_to(investigator, answer)

    def action_to_take(self, investigator, answer):
        method = getattr(self, self.ACTION_METHODS[self.action])
        return method(investigator, answer)

    def validate(self, answer):
        method = getattr(self, self.CONDITION_METHODS[self.condition])
        return method(answer)


class RandomHouseHoldSelection(BaseModel):
    mobile_number = models.CharField(max_length=10, unique=True, null=False, blank=False)
    no_of_households = models.PositiveIntegerField(null=True)
    selected_households = models.CharField(max_length=100, blank=False, null=False)

    def generate_new_list(self):
        selected_households = random.sample(list(range(1, self.no_of_households + 1)), NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR)
        selected_households.sort()
        self.selected_households = ",".join(str(x) for x in selected_households)
        self.save()

    def text_message(self):
        return "Dear investigator, these are the selected households: %s" % self.selected_households

    def generate(self, no_of_households):
        if not self.selected_households:
            self.no_of_households = no_of_households
            self.generate_new_list()
        investigator = Investigator(mobile_number=self.mobile_number)
        investigator.backend = Backend.objects.all()[0]
        send(self.text_message(), [investigator])


class Formula(BaseModel):
    name = models.CharField(max_length=50,unique=True, blank=False)
    numerator = models.ForeignKey(Question, blank=False, related_name="as_numerator")
    denominator = models.ForeignKey(Question, blank=False, related_name="as_denominator")
    batch = models.ForeignKey(Batch, null=True, related_name="formula")

    def clean(self, *args, **kwargs):
        if self.numerator.batch != self.denominator.batch:
            raise ValidationError('Numerator and Denominator must belong to the same batch')

    def save(self, *args, **kwargs):
        self.clean(*args, **kwargs)
        super(Formula, self).save(*args, **kwargs)

    def compute_for_location(self, location):
        investigators = Investigator.lives_under_location(location)
        if self.numerator.is_multichoice():
            return self.compute_multichoice_question_for_investigators(investigators)
        else:
            return self.compute_numerical_question_for_investigators(investigators)

    def compute_for_next_location_type_in_the_hierarchy(self, current_location):
        locations = current_location.get_children()
        data = {}
        for location in locations:
            data[location] = self.compute_for_location(location)
        return data

    def compute_numerical_question_for_investigators(self, investigators):
        values = []
        for investigator in investigators:
            values.append(self.compute_numerical_question_for_investigator(investigator))
        return sum(values)/len(values)

    def compute_multichoice_question_for_investigators(self, investigators):
        values = []
        computed_dict = {}
        for investigator in investigators:
            values.append(self.compute_multichoice_question_for_investigator(investigator))

        denominator = len(values)
        for option in self.numerator.options.all():
            numerator = sum([value[option.text] for value in values])
            computed_dict[option.text] = numerator / denominator
        return computed_dict

    def process_formula(self, numerator, denominator, investigator):
        return ((numerator * investigator.weights) / denominator) * 100

    def compute_multichoice_question_for_investigator(self, investigator):
        values = {}
        denominator = self.answer_sum_for_investigator(self.denominator, investigator)
        for option in self.numerator.options.all():
            numerator = self.compute_numerator_for_option(option, investigator)
            values[ option.text ] = self.process_formula(numerator, denominator, investigator)
        return values

    def compute_numerator_for_option(self, option, investigator):
        households = self.numerator.answer_class().objects.filter(investigator=investigator, answer=option).values_list('household', flat=True)
        return self.denominator.answer_class().objects.filter(household__in=households, question=self.denominator).aggregate(Sum('answer'))['answer__sum']

    def answer_sum_for_investigator(self, question, investigator):
        return question.answer_class().objects.filter(investigator=investigator, question=question).aggregate(Sum('answer'))['answer__sum']

    def answer_for_household(self, question, household):
        return question.answer_class().objects.get(household=household, question=question).answer

    def compute_numerical_question_for_investigator(self, investigator):
        denominator = self.answer_sum_for_investigator(self.denominator, investigator)
        numerator = self.answer_sum_for_investigator(self.numerator, investigator)
        return self.process_formula(numerator, denominator, investigator)

    def weight_for_location(self, location):
        investigator = Investigator.objects.filter(location=location)
        if investigator:
            return investigator[0].weights

    def compute_for_households_in_location(self, location):
        investigator = Investigator.objects.filter(location=location)
        household_data = {}
        if investigator:
            for household in investigator[0].households.all():
                household_data[household] = {
                    self.numerator: self.answer_for_household(self.numerator, household),
                    self.denominator: self.answer_for_household(self.denominator, household),
                }
        return household_data


class HouseholdMemberGroup(BaseModel):
    name = models.CharField(max_length=50)
    order = models.IntegerField(max_length=5, null=False, blank=False, unique=True, default=0)
    
    
class GroupCondition(BaseModel):
    CONDITIONS = {
                'EQUALS': 'EQUALS',
                'GREATER_THAN': 'GREATER_THAN',
                'LESS_THAN': 'LESS_THAN',
    }
    
    value = models.CharField(max_length=50)
    attribute = models.CharField(max_length=20, null=False)
    condition = models.CharField(max_length=20, null=False, default='EQUALS', choices=CONDITIONS.items())
    

def generate_auto_complete_text_for_location(location):
    auto_complete = LocationAutoComplete.objects.filter(location=location)
    if not auto_complete:
        auto_complete = LocationAutoComplete(location=location)
    else:
        auto_complete = auto_complete[0]
    parents = [location.name]
    while location.tree_parent:
        location = location.tree_parent
        parents.append(location.name)
    parents.reverse()
    auto_complete.text = " > ".join(parents)
    auto_complete.save()

@receiver(post_save, sender=Location)
def create_location_auto_complete_text(sender, instance, **kwargs):
    generate_auto_complete_text_for_location(instance)
    for location in instance.get_descendants():
        generate_auto_complete_text_for_location(location)


def auto_complete_text(self):
    return LocationAutoComplete.objects.get(location=self).text

Location.auto_complete_text = auto_complete_text
