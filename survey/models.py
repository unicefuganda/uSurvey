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

    def next_answerable_question(self):
        last_answered_question = self.last_answered_question()
        if not last_answered_question:
            return Survey.currently_open().first_question()
        else:
            return last_answered_question.next_question_for_investigator(self)

    def last_answered_question(self):
        answered = []
        for klass in [NumericalAnswer, TextAnswer, MultiChoiceAnswer]:
            try:
                answer = klass.objects.filter(investigator=self).latest()
                if answer: answered.append(answer)
            except ObjectDoesNotExist, e:
                pass
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def answered(self, question, household, answer):
        answer_class = question.answer_class()
        if answer_class == MultiChoiceAnswer:
            answer = question.options.get(order=int(answer))
        answer_class.objects.create(investigator=self, question=question, household=household, answer=answer)
        return question.next_question_for_investigator(self)

    def last_answer_for(self, question):
        answer_class = question.answer_class()
        return answer_class.objects.filter(investigator=self, question=question).latest()

    def reanswer(self, question):
        if getattr(self, 'ussd_variables', None):
            self.ussd_variables['REANSWER'].append(question)
        self.last_answer_for(question).delete()

class LocationAutoComplete(models.Model):
    location = models.ForeignKey(Location, null=True)
    text = models.CharField(max_length=500)

    class Meta:
        app_label = 'survey'

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
            return self.rule.action_to_take(investigator)
        else:
            raise ObjectDoesNotExist

    def next_question_for_investigator(self, investigator):
        answer = self.answer_class().objects.get(investigator=investigator, question=self)
        try:
            return self.get_next_question_by_rule(answer, investigator)
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

class HouseHold(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    investigator = models.ForeignKey(Investigator, null=True, related_name="households")

class Answer(BaseModel):
    investigator = models.ForeignKey(Investigator, null=True)
    household = models.ForeignKey(HouseHold, null=True)
    question = models.ForeignKey(Question, null=True)

    class Meta:
        app_label = 'survey'
        abstract = True
        get_latest_by = 'created'

class NumericalAnswer(Answer):
    answer = models.PositiveIntegerField(max_length=5, null=True)

    def save(self, *args, **kwargs):
        self.answer = int(self.answer)
        super(NumericalAnswer, self).save(*args, **kwargs)

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

    def end_interview(self, investigator):
        return None

    def skip_to(self, investigator):
        return self.next_question

    def reanswer(self, investigator):
        investigator.reanswer(self.question)
        if self.validate_with_question:
            investigator.reanswer(self.validate_with_question)
            return self.validate_with_question
        else:
            return self.question

    def ask_subquestion(self, investigator):
        return self.skip_to(investigator)

    def action_to_take(self, investigator):
        method = getattr(self, self.ACTION_METHODS[self.action])
        return method(investigator)

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