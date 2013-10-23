from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.db import models
from survey.models.households import Household, HouseholdMember
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

    IGNORED_CHARACTERS = "*!#';&"

    OPTIONS_PER_PAGE = 3
    PREVIOUS_PAGE_TEXT = "%s: Back" % getattr(settings,'USSD_PAGINATION',None).get('PREVIOUS')
    NEXT_PAGE_TEXT = "%s: Next" % getattr(settings,'USSD_PAGINATION',None).get('NEXT')

    identifier = models.CharField(max_length=100, blank=False, null=True)
    batches = models.ManyToManyField(Batch, null=True, related_name="questions")
    group = models.ForeignKey("HouseholdMemberGroup", null=True, related_name="question_group")
    text = models.CharField(max_length=150, blank=False, null=False)
    answer_type = models.CharField(max_length=15, blank=False, null=False, choices=TYPE_OF_ANSWERS)
    order = models.PositiveIntegerField(max_length=2, null=True)
    subquestion = models.BooleanField(default=False)
    parent = models.ForeignKey("Question", null=True, related_name="children")
    module = models.ForeignKey("QuestionModule", null=True, related_name="module_question")

    class Meta:
        app_label = 'survey'

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        if self.parent:
            self.subquestion = True

    def __unicode__(self):
        return "%s: (%s)" % (self.text, self.answer_type.upper())

    def clean(self, *args, **kwargs):
        if self.subquestion and self.order:
            raise ValidationError('Subquestions cannot have orders.')

        if self.subquestion and not self.parent:
            raise ValidationError('Subquestions must have parent questions.')

    def save(self, *args, **kwargs):
        self.clean(*args, **kwargs)
        super(Question, self).save(*args, **kwargs)

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

    def has_been_answered(self, member, batch):
        answer_class = self.answer_class()
        return len(answer_class.objects.filter(question=self, householdmember=member, batch=batch)) > 0

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
        all_rules = self.rule.all()
        for rule in all_rules:
            if rule.validate(answer):
                return rule.action_to_take(investigator, answer)

        raise ObjectDoesNotExist


    def next_question(self, location, member=None):
        order = self.parent.order if self.subquestion else self.order
        return self.batch.get_next_question(order, location=location)

    def to_ussd(self, page=1):
        if self.answer_type == self.MULTICHOICE:
            text = "%s\n%s" % (self.text, self.options_in_text(page))
            return text
        else:
            return self.text

    def get_subquestions(self):
        return Question.objects.filter(subquestion=True, parent=self)

    def rules_for_batch(self, batch):
        return self.rule.all().filter(batch=batch)

    def is_last_question_of_group(self):
        return self == self.group.last_question()

    def de_associate_from(self, batch):
        self.batches.remove(batch)
        batch_order_object = self.question_batch_order.filter(batch=batch)[0]
        all_remaining_batch_orders = batch.batch_question_order.all().filter(order__gt=batch_order_object.order)
        for batch_order in all_remaining_batch_orders:
            batch_order.order -= 1
            batch_order.save()
        batch_order_object.delete()


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
    householdmember = models.ForeignKey(HouseholdMember, null=True, related_name="%(class)s")
    question = models.ForeignKey(Question, null=True)
    batch = models.ForeignKey("Batch", null=True)
    rule_applied = models.ForeignKey("AnswerRule", null=True)
    is_old = models.BooleanField(default=False)

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
