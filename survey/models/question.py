from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import models
from survey.models.households import Household
from survey.models.investigator import Investigator
from survey.models.base import BaseModel
from survey.models.batch import Batch


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
    group = models.ForeignKey("HouseholdMemberGroup", null=True, related_name="question_group")
    text = models.CharField(max_length=150, blank=False, null=False)
    answer_type = models.CharField(max_length=15, blank=False, null=False, choices=TYPE_OF_ANSWERS)
    order = models.PositiveIntegerField(max_length=2, null=True)
    subquestion = models.BooleanField(default=False)
    parent = models.ForeignKey("Question", null=True, related_name="children")

    class Meta:
        app_label = 'survey'


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

    class Meta:
        app_label = 'survey'


    def to_text(self):
        return "%d: %s" % (self.order, self.text)


class Answer(BaseModel):
    investigator = models.ForeignKey(Investigator, null=True, related_name="%(class)s")
    household = models.ForeignKey(Household, null=True, related_name="%(class)s")
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
