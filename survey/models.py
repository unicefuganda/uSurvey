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
            return household.next_question()
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

    def next_question(self):
        last_question_answered = self.last_question_answered()
        if not last_question_answered:
            return Survey.currently_open().first_question()
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

class HouseholdHead(BaseModel):
    household = models.OneToOneField(Household, null=True, related_name="head")
    surname = models.CharField(max_length=12, blank=False, null=True)
    first_name = models.CharField(max_length=12, blank=False, null=True)
    age = models.PositiveIntegerField(validators=[MinValueValidator(10), MaxValueValidator(99)], null=True)
    male = models.BooleanField(default=True, verbose_name="Gender")
    occupation = models.CharField(max_length=100, blank=False, null=False, choices= OCCUPATION,
                                   verbose_name="Occupation / Main Livelihood", default="16")
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary', verbose_name="Highest level of education completed")
    resident_since = models.PositiveIntegerField(null=False, default=0,
     verbose_name = "How long has this household been resident in this village?")
    time_measure = models.CharField(max_length=7, null=False, choices=TIME_MEASURE, blank=False, default='Years')

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
   aged_between_15_49_years = models.PositiveIntegerField(blank=False, default=0, verbose_name="15-49 years?")

class Survey(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=255, blank=False, null=False)

    def first_question(self):
        return self.batches.reverse().latest('created').indicators.reverse().latest('order').questions.reverse().latest('order')

    @classmethod
    def currently_open(self):
        return Survey.objects.latest('created')

class Batch(BaseModel):
    survey = models.ForeignKey(Survey, null=True, related_name="batches")

class Indicator(BaseModel):
    batch = models.ForeignKey(Batch, null=True, related_name="indicators")
    order = models.PositiveIntegerField(max_length=2, null=True)

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
            return self.next_question()

    def next_question(self):
        order = self.parent.order if self.subquestion else self.order
        question = self.indicator.questions.filter(order=order + 1)
        if question:
            return question[0]

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
