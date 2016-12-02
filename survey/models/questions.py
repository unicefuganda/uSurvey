import os
import copy
import string
from django_rq import job
from collections import OrderedDict
from ordered_set import OrderedSet
from cacheops import cached_as
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.core.urlresolvers import reverse
from mptt.models import MPTTModel, TreeForeignKey
from model_utils.managers import InheritanceManager
from survey.models.interviews import Answer, MultiChoiceAnswer, MultiSelectAnswer, NumericalAnswer
from survey.models.householdgroups import HouseholdMemberGroup
from survey.models.access_channels import USSDAccess, InterviewerAccess
from survey.models.base import BaseModel
from survey.models.households import Household
from survey.models.generics import GenericQuestion
from survey.models.interviews import AnswerAccessDefinition
from survey.models.access_channels import ODKAccess

ALL_ANSWERS = Answer.answer_types()


class Question(GenericQuestion):
    objects = InheritanceManager()
    qset = models.ForeignKey('QuestionSet', related_name='questions')
    mandatory = models.BooleanField(default=True)

    class Meta:
        abstract = False
        unique_together = [('identifier', 'qset'), ]

    def answers(self):
        return Answer.get_class(self.answer_type).objects.filter(question=self)

    def validators(self):
        return Answer.get_class(self.answer_type).validators()

    def validator_names(self):
        return [v.__name__ for v in Answer.get_class(self.answer_type).validators()]

    # just utility to get number of times this question has been answered
    def total_answers(self):
        return Answer.get_class(self.answer_type).objects.filter(question=self).count()

    def delete(self, using=None):
        '''
        Delete related answers before deleting this object
        :param using:
        :return:
        '''
        answer_class = Answer.get_class(self.answer_type)
        answer_class.objects.filter(question=self).delete()
        return super(Question, self).delete(using=using)

    def display_text(self, channel=None):
        text = self.text
        if channel and channel == USSDAccess.choice_name() and self.answer_type == MultiChoiceAnswer.choice_name():
            extras = []
            # append question options
            for option in self.options.all().order_by('order'):
                extras.append(option.to_text)
            text = '%s\n%s' % (text, '\n'.join(extras))
        return text

    def next_question(self, reply):
        flows = self.flows.all()
        answer_class = Answer.get_class(self.answer_type)
        resulting_flow = None
        for flow in flows:
            if flow.validation_test:
                test_values = [arg.param for arg in flow.text_arguments]
                if getattr(answer_class, flow.validation_test)(reply, *test_values) == True:
                    resulting_flow = flow
                    break
            else:
                resulting_flow = flow
        if resulting_flow:
            return resulting_flow.next_question

    def previous_inlines(self):
        return self.qset.previous_inlines(self)

    def upcoming_inlines(self):
        return self.qset.upcoming_inlines(self)

    def direct_sub_questions(self):
        from survey.forms.logic import LogicForm
        sub_flows = self.flows.filter(
            desc=LogicForm.SUBQUESTION_ACTION, validation_test__isnull=False)
        return OrderedSet([flow.next_question for flow in sub_flows])

    def conditional_flows(self):
        return self.flows.filter(validation_test__isnull=False)

    def preceeding_conditional_flows(self):
        return self.connecting_flows.filter(validation_test__isnull=False)

    def __unicode__(self):
        return "%s - %s: (%s)" % (self.identifier, self.text, self.answer_type.upper())

    def save(self, *args, **kwargs):
        if self.answer_type not in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()]:
            self.options.all().delete()
        return super(Question, self).save(*args, **kwargs)

    @classmethod
    def index_breadcrumbs(cls, **kwargs):
        if kwargs.has_key('qset'):
            return kwargs['qset'].edit_breadcrumbs(**kwargs)  # important to select correct type
        return []

    @classmethod
    def edit_breadcrumbs(cls, **kwargs):
        breadcrumbs = cls.index_breadcrumbs(**kwargs)
        breadcrumbs.append((kwargs['qset'].name, reverse('qset_questions_page',  args=(kwargs['qset'].pk, ))))
        return breadcrumbs

    @classmethod
    def new_breadcrumbs(cls, **kwargs):
        breadcrumbs = cls.index_breadcrumbs(**kwargs)
        return cls.edit_breadcrumbs(**kwargs)

    @classmethod
    def zombies(cls,  qset):
        # these are the qset questions that do not belong to any flow in any
        # way
        flow_questions = qset.flow_questions
        return qset.questions.exclude(pk__in=[q.pk for q in flow_questions])

    def hierarchical_result_for(self, location_parent, survey):
        locations = location_parent.get_children().order_by('name')[:10]
        answers = self.multichoiceanswer.all()
        return self._format_answer(locations, answers, survey)

    def _format_answer(self, locations, answers, survey):
        question_options = self.options.all()
        data = OrderedDict()
        for location in locations:
            households = Household.all_households_in(location, survey)
            data[location] = {option.text: answers.filter(value=option, interview__householdmember__household__in=households).count() for option in
                              question_options}
        return data


class QuestionFlow(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    question = models.ForeignKey(Question, related_name='flows')
    question_type = models.CharField(max_length=100)
    validation_test = models.CharField(
        max_length=200, null=True, blank=True, choices=VALIDATION_TESTS)
    # if validation passes, classify this flow response as having this value
    name = models.CharField(max_length=200, null=True, blank=True)
    # this would provide a brief description of this flow
    desc = models.CharField(max_length=200, null=True, blank=True)
    next_question = models.ForeignKey(
        Question, related_name='connecting_flows', null=True, blank=True, on_delete=models.SET_NULL)
    next_question_type = models.CharField(max_length=100)

    class Meta:
        app_label = 'survey'
        # unique_together = [('question', 'next_question', 'desc', ),]

    @property
    def test_params(self):
        return [t.param for t in self.text_arguments]

    def params_display(self):
        params = []
        for arg in self.text_arguments:
            if self.question.answer_type == MultiChoiceAnswer.choice_name():
                params.append(self.question.options.get(order=arg.param).text)
            else:
                params.append(arg.param)

        return params

    @property
    def text_arguments(self):
        return TextArgument.objects.filter(flow=self).order_by('position')

    @property
    def test_arguments(self):
        return TextArgument.objects.filter(flow=self).order_by('position')

    def save(self, *args, **kwargs):
        self.question_type = self.question.type_name()
        if self.next_question:
            self.next_question_type = self.next_question.type_name()
        return super(QuestionFlow, self).save(*args, **kwargs)


class TestArgument(BaseModel):
    object = InheritanceManager()
    flow = models.ForeignKey(QuestionFlow, related_name='%(class)s')
    position = models.PositiveIntegerField()

    @classmethod
    def argument_types(cls):
        return [cl.__name__ for cl in cls.__subclasses__()]

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'


class TextArgument(TestArgument):
    param = models.TextField()

    class Meta:
        app_label = 'survey'


class NumberArgument(TestArgument):
    param = models.IntegerField()

    class Meta:
        app_label = 'survey'


class DateArgument(TestArgument):
    param = models.DateField()

    class Meta:
        app_label = 'survey'


class QuestionOption(BaseModel):
    question = models.ForeignKey(Question, null=True, related_name="options")
    text = models.CharField(max_length=150, blank=False, null=False)
    order = models.PositiveIntegerField()

    class Meta:
        app_label = 'survey'
        ordering = ['order', ]

    @property
    def to_text(self):
        return "%d: %s" % (self.order, self.text)

    def __unicode__(self):
        return self.text


class QuestionSet(BaseModel):   # can be qset, listing, respondent personal
    objects = InheritanceManager()
    name = models.CharField(max_length=100, blank=False, null=True, db_index=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    start_question = models.OneToOneField(
        Question, related_name='starter_%(class)s', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return "%s" % self.name

    def can_be_deleted(self):
        return True, ''

    def get_loop_story(self):
        '''
        Basically returns all the loops which a question is involved in. This retains the queston order
        :return:
        '''
        @cached_as(QuestionLoop.objects.filter(loop_starter__qset__id=self.id))
        def _loop_story():
            inlines = self.questions_inline()
            loops = []
            loop_story = OrderedDict()
            for inline_ques in inlines:
                if hasattr(inline_ques, 'loop_started'):
                    loops.append(inline_ques.loop_started)
                loop_story[inline_ques.pk] = copy.deepcopy(loops)
                #also include all direct subquestions
                map(lambda q: loop_story.update({q.pk: copy.deepcopy(loops)}), inline_ques.direct_sub_questions())
                if hasattr(inline_ques, 'loop_ended'):
                    loops.pop(-1)
            return loop_story
        return _loop_story()

    def non_response_enabled(self, ea):
        locations = set()
        ea_locations = ea.locations.all()
        if ea_locations:
            map(lambda loc: locations.update(
                loc.get_ancestors(include_self=True)), ea_locations)
        return self.open_locations.filter(non_response=True, location__pk__in=[location.pk
                                                                               for location in locations]).exists()

    @property
    def answer_types(self):
        access_channels = self.access_channels.values_list(
            'channel', flat=True)
        return set(AnswerAccessDefinition.objects.filter(channel__in=access_channels).values_list('answer_type',
                                                                                                  flat=True))

    def next_inline(self, question, channel=ODKAccess.choice_name()):
        qflows = QuestionFlow.objects.filter(question__qset=self, validation_test__isnull=True)
        if qflows.exists():
            return next_inline_question(question, qflows, AnswerAccessDefinition.answer_types(channel))

    def last_question_inline(self):
        qflows = QuestionFlow.objects.filter(
            question__qset=self, validation_test__isnull=True)
        if qflows.exists():
            return last_inline(self.start_question, qflows)
        else:
            return self.start_question

    def questions_inline(self):
        qflows = QuestionFlow.objects.filter(
            question__qset=self, validation_test__isnull=True)
        if self.start_question:
            inlines = inline_questions(self.start_question, qflows)
            if inlines and inlines[-1] is None:
                inlines.pop(-1)
            return inlines
        else:
            return []

    def previous_inlines(self, question):
        inlines = self.questions_inline()
        q_index = None
        for idx, q in enumerate(inlines):
            if q.identifier == question.identifier:
                q_index = idx
                break
        if q_index is None:
            raise ValidationError('%s not inline' % question.identifier)
        return set(inlines[:idx])

    def upcoming_inlines(self, question):
        inlines = list(self.questions_inline())
        q_index = None
        for idx, q in enumerate(inlines):
            if q.identifier == question.identifier:
                q_index = idx
                break
        if q_index is None:
            raise ValidationError('%s not inline' % question.identifier)
        return set(inlines[q_index:])

    def inlines_between(self, start_question, end_question):
        inlines = list(self.questions_inline())
        start_index = None
        end_index = None
        for idx, q in enumerate(inlines):
            if q.identifier == start_question.identifier:
                if end_index:
                    raise ValidationError('End question before start')
                start_index = idx
            if q.identifier == start_question.identifier:
                end_index = idx
                break
        if start_index is None or end_index is None:
            raise ValidationError('%s not inline' % start_question.identifier)
        return set(inlines[start_index:end_index])

    def zombie_questions(self):
        return Question.zombies(self)

    @property
    def flow_questions(self):
        # @cached_as(Question.objects.filter(qset__id=self.id)) # to find out best caching for this.
        def _flow_questions():
            inline_ques = self.questions_inline()
            questions = OrderedSet(inline_ques)
            flow_questions = OrderedSet()
            for ques in inline_ques:
                flow_questions.append(ques)
                # boldly assuming subquests dont go
                map(lambda q: flow_questions.add(
                    q), ques.direct_sub_questions())
                # more than quest subquestion deep for present implemnt
            return flow_questions
        return _flow_questions()

    def activate_non_response_for(self, location):
        self.open_locations.filter(location=location).update(non_response=True)

    def deactivate_non_response_for(self, location):
        self.open_locations.filter(
            location=location).update(non_response=False)

    @classmethod
    def index_breadcrumbs(cls, **kwargs):
        return []

    @classmethod
    def edit_breadcrumbs(cls, **kwargs):
        breadcrumbs = cls.index_breadcrumbs(**kwargs)
        if kwargs.has_key('qset'):
            cls = kwargs['qset'].__class__
        breadcrumbs.append((cls.verbose_name(), reverse('%s_home' % cls.resolve_tag())))
        return breadcrumbs

    @classmethod
    def new_breadcrumbs(cls, *args, **kwargs):
        return cls.edit_breadcrumbs(**kwargs)

# @job
# def refresh_loop_story(qset):
#     for


def next_inline_question(question, flows, answer_types=ALL_ANSWERS):
    if answer_types is None:
        answer_types = ALL_ANSWERS
    try:
        qflow = flows.get(question=question, validation_test__isnull=True)
        next_question = qflow.next_question
        if next_question and next_question.answer_type in answer_types:
            return next_question
        else:
            return next_inline_question(next_question, flows, answer_types=answer_types)
    except QuestionFlow.DoesNotExist:
        return None


def last_inline(question, flows):
    try:
        qflow = flows.get(
            question=question, validation_test__isnull=True, next_question__isnull=False)
        return last_inline(qflow.next_question, flows)
    except QuestionFlow.DoesNotExist:
        return question


def first_inline_flow_with_desc(question, desc):
    try:
        if question.flows.filter(desc=desc).exists():
            return question.flows.get(desc=desc)
        if question.connecting_flows.filter(desc=desc).exists():
            return None
        iflow = question.flows.get(
            validation_test__isnull=True, next_question__isnull=False)
        return first_inline_flow_with_desc(iflow.next_question, desc)
    except QuestionFlow.DoesNotExist:
        return None


def inline_questions(question, flows):
    # to do, optimize this function
    # questions = [Question.get(pk=question.pk), ]
    questions = [question, ]
    try:
        qflow = flows.get(question=question, validation_test__isnull=True)
        questions.extend(inline_questions(qflow.next_question, flows))
    except QuestionFlow.DoesNotExist:
        pass
    return questions


def inline_flows(question, flows):
    flows = []
    try:
        qflow = flows.get(question=question, validation_test__isnull=True)
        flows.append(qflow)
        flows.extend(inline_questions(qflow.next_question, flows))
    except QuestionFlow.DoesNotExist:
        pass
    return flows


class QuestionSetChannel(BaseModel):
    ACCESS_CHANNELS = [(name, name)
                       for name in InterviewerAccess.access_channels()]
    qset = models.ForeignKey(QuestionSet, related_name='access_channels')
    channel = models.CharField(max_length=100, choices=ACCESS_CHANNELS)

    class Meta:
        app_label = 'survey'
        unique_together = ('qset', 'channel')


class LoopCount(BaseModel):
    loop = models.OneToOneField('QuestionLoop', related_name="%(class)s")

    @classmethod
    def choice_name(cls):
        return cls.__name__.lower()

    def get_count(self, interview):
        pass

    class Meta:
        abstract = True


class FixedLoopCount(LoopCount):
    value = models.PositiveIntegerField()

    def get_count(self, interview):
        return self.value

    def odk_get_count(self):
        return self.get_count()


class PreviousAnswerCount(LoopCount):
    value = models.ForeignKey(Question, related_name='loop_count_identifier')

    def get_count(self, interview):
        return interview.numericalanswer.filter(question=self.value).value      #  previous question must be numeric

    def odk_get_count(self, interview):
        raise Exception('need to do!') #to do

    def save(self, *args, **kwargs):
        if self.value.answer_type != NumericalAnswer.choice_name():
            raise ValidationError('Loop count can only be a number')
        return super(PreviousAnswerCount, self).save(*args, **kwargs)


class QuestionLoop(BaseModel):
    USER_DEFINED = ''
    FIXED_REPEATS = FixedLoopCount.choice_name()
    PREVIOUS_QUESTION = PreviousAnswerCount.choice_name()
    REPEAT_OPTIONS = [(USER_DEFINED, 'User Defined'),
                       (FIXED_REPEATS, 'Fixed number of Repeats'),
                       (PREVIOUS_QUESTION, 'Response from previous question'),
                       ]
    loop_label = models.CharField(max_length=64)
    loop_starter = models.OneToOneField(Question, related_name='loop_started')
    repeat_logic = models.CharField(max_length=64, choices=REPEAT_OPTIONS)
    loop_ender = models.OneToOneField(Question, related_name='loop_ended')

    def loop_questions(self):
        return self.loop_starter.qset.inlines_between(self.loop_starter, self.loop_ender)






