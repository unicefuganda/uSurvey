from django.db import models
from django.core.validators import *
from django_extensions.db.models import TimeStampedModel
from rapidsms.contrib.locations.models import Location
from django.db.models.signals import post_save
from django.dispatch import receiver
from investigator_configs import *
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.conf import settings
from django.core.cache import cache
import datetime

class BaseModel(TimeStampedModel):
    class Meta:
        app_label = 'survey'
        abstract = True

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
                if answer: answered.append(answer)
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
            if next_question == None or next_question.indicator.batch != question.indicator.batch:
                household.batch_completed(question.indicator.batch)
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

    def households_list(self, page = 1):
        all_households = list(self.all_households())
        paginator = Paginator(all_households, self.HOUSEHOLDS_PER_PAGE)
        households = paginator.page(page)
        households_list = []
        for household in households:
            text = "%s: %s" % (all_households.index(household) + 1, household.head.surname)
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

    def has_open_batch(self):
        locations = self.location.get_ancestors(include_self=True)
        return BatchLocationStatus.objects.filter(location__in = locations).count() > 0

    def was_active_within(self, minutes):
        last_answered = self.last_answered()
        if not last_answered:
            return False
        last_active = last_answered.created
        timeout = datetime.datetime.utcnow().replace(tzinfo=last_active.tzinfo) - datetime.timedelta(minutes=minutes)
        return last_active >= timeout

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

    def next_question(self, last_question_answered = None):
        if not last_question_answered:
            last_question_answered = self.last_question_answered()
        if not last_question_answered:
            open_batch = Batch.currently_open_for(location = self.investigator.location)
            if open_batch:
                return open_batch.first_question()
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
        for klass in [NumericalAnswer, TextAnswer, MultiChoiceAnswer]:
            klass.objects.filter(household=self).delete()

    def has_completed_batch(self, batch):
        return self.completed_batches.filter(batch=batch).count() > 0

    def batch_completed(self, batch):
        return self.completed_batches.get_or_create(household=self, investigator=self.investigator, batch=batch)

    def batch_reopen(self, batch):
        self.completed_batches.filter(household=self).delete()

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

class Survey(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=255, blank=False, null=False)

    def get_next_open_batch(self, order, location):
        next_batch_in_order = self.batches.filter(order__gt = order).order_by('order')
        next_open_batch = location.open_batches.filter(batch__in = next_batch_in_order)
        if next_open_batch:
            return next_open_batch[0].batch

class Batch(BaseModel):
    survey = models.ForeignKey(Survey, null=True, related_name="batches")
    order = models.PositiveIntegerField(max_length=2, null=True)

    @classmethod
    def currently_open_for(self, location):
        locations = location.get_ancestors(include_self=True)
        open_batches = BatchLocationStatus.objects.filter(location__in = locations)
        if open_batches.count() > 0:
            return open_batches.order_by('created').all()[:1].get().batch

    def first_question(self):
        return self.indicators.get(order=1).questions.get(order=1)

    def open_for_location(self, location):
        return self.open_locations.get_or_create(batch=self, location=location)

    def close_for_location(self, location):
        self.open_locations.filter(batch=self).delete()

    def get_next_indicator(self, order, location):
        indicator = self.indicators.filter(order = order + 1)
        if indicator:
            return indicator[0]
        else:
            return self.get_indicator_from_next_open_batch(location = location)

    def get_indicator_from_next_open_batch(self, location):
        next_open_batch = self.survey.get_next_open_batch(order = self.order, location = location)
        if next_open_batch:
            return next_open_batch.get_next_indicator(order = 0, location = location)

class BatchLocationStatus(BaseModel):
    batch = models.ForeignKey(Batch, null=True, related_name="open_locations")
    location = models.ForeignKey(Location, null=True, related_name="open_batches")

class HouseholdBatchCompletion(BaseModel):
    household = models.ForeignKey(Household, null=True, related_name="completed_batches")
    batch = models.ForeignKey(Batch, null=True, related_name="completed_households")
    investigator = models.ForeignKey(Investigator, null=True, related_name="completed_batches")

class Indicator(BaseModel):
    batch = models.ForeignKey(Batch, null=True, related_name="indicators")
    order = models.PositiveIntegerField(max_length=2, null=True)

    def get_next_question(self, order, location):
        question = self.questions.filter(order=order + 1)
        if question:
            return question[0]
        else:
            return self.get_question_from_next_indicator(location = location)

    def get_question_from_next_indicator(self, location):
        next_indicator = self.batch.get_next_indicator(order = self.order, location = location)
        if next_indicator:
            return next_indicator.get_next_question(order = 0, location = location)

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

    indicator = models.ForeignKey(Indicator, null=True, related_name="questions")
    text = models.CharField(max_length=60, blank=False, null=False)
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
            return self.next_question(location = household.investigator.location)

    def next_question(self, location):
        order = self.parent.order if self.subquestion else self.order
        return self.indicator.get_next_question(order, location = location)

    def to_ussd(self, page=1):
        if self.answer_type == self.MULTICHOICE:
            text = "%s\n%s" % (self.text, self.options_in_text(page))
            return text
        else:
            return self.text

class QuestionOption(BaseModel):
    question = models.ForeignKey(Question, null=True, related_name="options")
    text = models.CharField(max_length=20, blank=False, null=False)
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
    auto_complete.text = ", ".join(parents)
    auto_complete.save()

@receiver(post_save, sender=Location)
def create_location_auto_complete_text(sender, instance, **kwargs):
    generate_auto_complete_text_for_location(instance)
    for location in instance.get_descendants():
        generate_auto_complete_text_for_location(location)

def auto_complete_text(self):
    return LocationAutoComplete.objects.get(location=self).text

Location.auto_complete_text = auto_complete_text
