import copy
from collections import OrderedDict
from ordered_set import OrderedSet
from cacheops import cached_as
from cacheops import invalidate_obj
from django_cloneable import CloneableMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.core.urlresolvers import reverse
from model_utils.managers import InheritanceManager
from survey.models.interviews import Answer, MultiChoiceAnswer, MultiSelectAnswer, NumericalAnswer, AutoResponse
from survey.models.access_channels import USSDAccess, InterviewerAccess
from survey.models.base import BaseModel
from survey.models.generics import GenericQuestion
from survey.models.interviews import AnswerAccessDefinition
from survey.models.access_channels import ODKAccess
from survey.models.surveys import Survey
from survey.models.response_validation import ResponseValidation

ALL_ANSWERS = Answer.answer_types()


class Question(CloneableMixin, GenericQuestion):
    objects = InheritanceManager()
    qset = models.ForeignKey('QuestionSet', related_name='questions')
    mandatory = models.BooleanField(default=True)

    class Meta:
        abstract = False
        unique_together = [('identifier', 'qset'), ]
        ordering = ('modified', 'created')

    @classmethod
    def get(cls, **kwargs):
        from survey.models import BatchQuestion
        try:    # this is just a quick fix till I find out why Question.get doesnt seem to find BatchQuestions
            return BatchQuestion.objects.get(**kwargs)
        except BatchQuestion.DoesNotExist:
            return super(Question, cls).get(**kwargs)

    @property
    def e_qset(self):
        """This one basically means exact question set. Should retrieve batch, Listing template, etc
        :return:
        """
        return QuestionSet.get(pk=self.qset.pk)

    def answers(self):
        return Answer.get_class(self.answer_type).objects.filter(question=self)

    def loops(self):
        return self.qset.get_loop_story().get(self.pk, [])

    # just utility to get number of times this question has been answered
    def total_answers(self):
        return Answer.get_class(
            self.answer_type).objects.filter(
            question=self).count()

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
        if channel and channel == USSDAccess.choice_name(
        ) and self.answer_type == MultiChoiceAnswer.choice_name():
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
                if getattr(
                        answer_class,
                        flow.validation_test)(
                        reply,
                        *test_values) is True:
                    resulting_flow = flow
                    break
            else:
                resulting_flow = flow
        if resulting_flow and resulting_flow.next_question:
            # better for it to know who it is
            return Question.get(id=resulting_flow.next_question.id)

    def previous_inlines(self):
        return self.qset.previous_inlines(self)

    def upcoming_inlines(self):
        return self.qset.upcoming_inlines(self)

    def upcoming_question(self):
        return self.qset.next_inline()

    def upcoming_flow_questions(self):
        questions = OrderedSet()
        started = False
        for q in self.qset.flow_questions:
            if q.pk == self.pk:
                started = True
            if started:
                questions.append(q)
        return questions

    def direct_sub_questions(self):
        from survey.forms.logic import LogicForm
        sub_flows = self.flows.filter(
            desc=LogicForm.SUBQUESTION_ACTION, validation__isnull=False)
        return OrderedSet([flow.next_question for flow in sub_flows])

    def conditional_flows(self):
        return self.flows.filter(validation__isnull=False)

    def preceeding_conditional_flows(self):
        return self.connecting_flows.filter(validation__isnull=False)

    def __unicode__(self):
        return " - ".join([self.identifier, self.text])

    def save(self, *args, **kwargs):
        if self.answer_type not in [
                MultiChoiceAnswer.choice_name(),
                MultiSelectAnswer.choice_name()]:
            self.options.all().delete()
        invalidate_obj(self.qset)       # to fix update of flow_question update
        return super(Question, self).save(*args, **kwargs)

    @classmethod
    def index_breadcrumbs(cls, **kwargs):
        if 'qset' in kwargs:
            return kwargs['qset'].edit_breadcrumbs(
                **kwargs)  # important to select correct type
        return []

    @classmethod
    def edit_breadcrumbs(cls, **kwargs):
        breadcrumbs = cls.index_breadcrumbs(**kwargs)
        breadcrumbs.append(
            (kwargs['qset'].name, reverse(
                'qset_questions_page', args=(
                    kwargs['qset'].pk, ))))
        return breadcrumbs

    @classmethod
    def new_breadcrumbs(cls, **kwargs):
        cls.index_breadcrumbs(**kwargs)
        return cls.edit_breadcrumbs(**kwargs)

    @classmethod
    def zombies(cls, qset):
        # these are the qset questions that do not belong to any flow in any
        # way
        flow_questions = qset.flow_questions
        return qset.questions.exclude(pk__in=[q.pk for q in flow_questions])

    def hierarchical_result_for(self, location_parent, survey):
        locations = location_parent.get_children().order_by('name')[:10]
        answers = self.multichoiceanswer.all()
        return self._format_answer(locations, answers, survey)

    @property
    def loop_story(self):
        return self.qset.get_loop_story().get(self.id, [])


class QuestionFlow(CloneableMixin, BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    question = models.ForeignKey(Question, related_name='flows')
    question_type = models.CharField(max_length=100)
    validation = models.ForeignKey(ResponseValidation, null=True, blank=True)
    # if validation passes, classify this flow response as having this value
    name = models.CharField(max_length=200, null=True, blank=True)
    # this would provide a brief description of this flow
    desc = models.CharField(max_length=200, null=True, blank=True)
    next_question = models.ForeignKey(
        Question,
        related_name='connecting_flows',
        null=True,
        blank=True,
        on_delete=models.SET_NULL)
    next_question_type = models.CharField(max_length=100)

    def params_display(self):
        return self.text_arguments.values_list('param', flat=True)

    @property
    def validation_test(self):
        if self.validation:
            return self.validation.validation_test

    @validation_test.setter
    def validation_test(self, test):
        if self.validation:
            self.validation.validation_test = test
        else:
            self.validation = ResponseValidation.objects.create(validation_test=test)

    class Meta:
        app_label = 'survey'
        # unique_together = [('question', 'next_question', 'desc', ),]

    @property
    def test_params(self):
        if self.validation:
            return self.validation.test_params

    @property
    def text_arguments(self):
        if self.validation:
            return self.validation.text_arguments
        else:
            from survey.models import TextArgument
            return TextArgument.objects.none()

    @property
    def test_arguments(self):
        if self.validation:
            return self.validation.test_arguments
        else:
            from survey.models import TextArgument
            return TextArgument.objects.none()

    def save(self, *args, **kwargs):
        invalidate_obj(self.question)
        invalidate_obj(QuestionSet.get(pk=self.question.qset.pk))
        if self.next_question:
            invalidate_obj(self.next_question)
        return super(QuestionFlow, self).save(*args, **kwargs)


class QuestionOption(CloneableMixin, BaseModel):
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


class QuestionSet(CloneableMixin, BaseModel):   # can be qset, listing, respondent personal
    objects = InheritanceManager()
    name = models.CharField(
        max_length=100,
        db_index=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    start_question = models.OneToOneField(
        Question,
        related_name='qset_started',
        null=True,
        blank=True,
        on_delete=models.SET_NULL)

    @property
    def to_exact(self):
        """This one basically means exact question set. Should retrieve batch, Listing template, etc
        :return:
        """
        return self.get(pk=self.pk)

    @classmethod
    def question_model(cls):
        return Question

    class Meta:
        app_label = 'survey'
        ordering = ('modified', 'created')

    def __unicode__(self):
        return "%s" % self.name

    def can_be_deleted(self):
        return True, ''

    @property
    def auto_fields(self):
        return self.questions.filter(answer_type=AutoResponse.choice_name())

    @property
    def all_questions(self):
        return self.flow_questions

    def get_loop_story(self):
        """
        Basically returns all the loops which a question is involved in. This retains the queston order
        :return:
        """
        @cached_as(QuestionSet.objects.get(id=self.id),
                   QuestionLoop.objects.filter(loop_starter__qset__id=self.id),
                   Question.objects.filter(qset__id=self.id))
        def _loop_story():
            inlines = self.questions_inline()
            loops = []
            loop_story = OrderedDict()
            for inline_ques in inlines:
                if hasattr(inline_ques, 'loop_started'):
                    loops.append(inline_ques.loop_started)
                loop_story[inline_ques.pk] = copy.deepcopy(loops)
                # also include all direct subquestions
                map(lambda q: loop_story.update(
                    {q.pk: copy.deepcopy(loops)}), inline_ques.direct_sub_questions())
                if hasattr(inline_ques, 'loop_ended'):
                    loops.pop(-1)
            return loop_story
        return _loop_story()

    @property
    def has_loop(self):
        return QuestionLoop.objects.filter(
            loop_starter__qset__pk=self.pk).exists()

    @property
    def has_skip(self):
        from survey.forms.logic import LogicForm
        return QuestionFlow.objects.filter(
            question__qset__pk=self.pk,
            desc=LogicForm.SKIP_TO).exists()

    def non_response_enabled(self, ea):
        locations = []
        ea_locations = ea.locations.all()
        if ea_locations:
            map(lambda loc: locations.extend(
                loc.get_ancestors(include_self=True)), ea_locations)
        return self.open_locations.filter(
            non_response=True, location__pk__in=[
                location.pk for location in locations]).exists()

    def inline_flows(self):
        return QuestionFlow.objects.filter(
            question__qset__id=self.id,
            validation__isnull=True,
            next_question__isnull=False)

    @property
    def answer_types(self):
        access_channels = self.access_channels.values_list(
            'channel', flat=True)
        return set(
            AnswerAccessDefinition.objects.filter(
                channel__in=access_channels).values_list(
                'answer_type', flat=True))

    def next_inline(self, question, channel=ODKAccess.choice_name()):
        @cached_as(
            QuestionSet.objects.get(
                id=self.id), QuestionLoop.objects.filter(
                loop_starter__qset__id=self.id), Question.objects.filter(
                qset__id=self.id), self.inline_flows())
        def _next_inline():
            qflows = self.inline_flows()
            if qflows.exists():
                return next_inline_question(
                    question, qflows, AnswerAccessDefinition.answer_types(channel))
        return _next_inline()

    def last_question_inline(self):
        qflows = self.inline_flows()
        if qflows.exists():
            return last_inline(self.start_question, qflows)
        else:
            return self.start_question

    def questions_inline(self):
        qflows = self.inline_flows()
        start_question_id = None

        @cached_as(QuestionSet.objects.get(id=self.id),
                   Question.objects.filter(qset__id=self.id),
                   QuestionFlow.objects.filter(question__qset__id=self.id),
                   QuestionFlow.objects.filter(next_question__qset__id=self.id),
                   QuestionLoop.objects.filter(loop_starter__qset__id=self.id))
        def _questions_inline():
            if self.start_question:
                inlines = inline_questions(self.start_question, qflows)
                if inlines and inlines[-1] is None:
                    inlines.pop(-1)
                # this is to convert question to correct type
                inlines = [Question.get(pk=q.pk) for q in inlines]
                return inlines
            else:
                return []
        return _questions_inline()

    def previous_inlines(self, question):
        inlines = self.questions_inline()
        q_index = None
        for idx, q in enumerate(inlines):
            if q.identifier == question.identifier:
                q_index = idx
                break
        if q_index is None:
            raise ValidationError('%s not inline' % question.identifier)
        return OrderedSet(inlines[:idx])

    def upcoming_inlines(self, question):
        inlines = list(self.questions_inline())
        q_index = None
        for idx, q in enumerate(inlines):
            if q.identifier == question.identifier:
                q_index = idx
                break
        if q_index is None:
            raise ValidationError('%s not inline' % question.identifier)
        return OrderedSet(inlines[q_index:])

    def inlines_between(self, start_question, end_question):
        inlines = list(self.questions_inline())
        start_index = 0
        end_index = 0
        for idx, q in enumerate(inlines):
            if q.identifier == start_question.identifier:
                if end_index:
                    raise ValidationError('End question before start')
                start_index = idx
            if q.identifier == end_question.identifier:
                end_index = idx
                break
        if start_index is None or end_index is None:
            raise ValidationError('%s not inline' % start_question.identifier)
        return OrderedSet(inlines[start_index:end_index])

    def zombie_questions(self):
        return Question.zombies(self)

    @property
    def flow_questions(self):
        # @cached_as(Question.objects.filter(qset__id=self.id)) # to find out best caching for this.
        def _flow_questions():
            # next line is to normalize to question set. Otherwise it seems to be causing some issues with flows
            # since the flow is more native to Qset. Additional attributes in subclasses are just extras
            qset = QuestionSet.get(id=self.id)
            inline_ques = qset.questions_inline()
            OrderedSet(inline_ques)
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
        if 'qset' in kwargs:
            cls = kwargs['qset'].__class__
        breadcrumbs.append(
            (cls.verbose_name(), reverse(
                '%s_home' %
                cls.resolve_tag())))
        if 'qset' in kwargs:
            breadcrumbs.append((kwargs['qset'],reverse('qset_questions_page',kwargs={'qset_id':kwargs.get('qset').id})))
        return breadcrumbs

    @classmethod
    def new_breadcrumbs(cls, *args, **kwargs):
        return cls.edit_breadcrumbs(**kwargs)

    @property
    def g_first_question(self):
        questions = self.all_questions
        if questions:
            return Question.get(pk=questions[0].id)

    def survey_list(self):
        survey_names = []
        survey_names.extend(Survey.objects.filter(listing_form_id=self.id))
        survey_names.extend(Survey.objects.filter(preferred_listing_id=self.id))
        return survey_names

    def deep_clone(self, **attrs):
        import random
        batch = QuestionSet.get(pk=self.pk)
        old_batch = batch
        start_question = batch.start_question
        attrs.update({'start_question': None, 'name': '%s-copy-%s' % (batch.name, random.randrange(1000))})
        batch = batch.clone(attrs=attrs)
        flows = QuestionFlow.objects.filter(question__qset=old_batch)
        if start_question:
            start_question_id = start_question.id
            if flows.exists():
                # now clone all flows for this batch.
                treated = {}
                flows = QuestionFlow.objects.filter(
                    question__qset__id=old_batch.id)
                for flow in flows:
                    # except for the first question, every other is a next
                    # question
                    question = flow.question
                    old_question_id = question.id
                    question = treated.get(question.identifier, None)
                    if question is None:
                        question = Question.get(
                            pk=flow.question.pk).clone(
                            attrs={
                                'qset': batch})
                        for option in flow.question.options.all():
                            # to do, appearantly clone question_opt not workng
                            QuestionOption.objects.create(
                                question=question, order=option.order, text=option.text)
                        treated[question.identifier] = question
                        if old_question_id == start_question_id:
                            batch.start_question = question
                            # just take this opportunity to update the access
                            # channels once
                            for channel in old_batch.access_channels.all():
                                channel.clone(attrs={'qset': batch})
                            batch.save()
                    next_question = flow.next_question
                    if next_question:
                        next_question = treated.get(
                            next_question.identifier, None)
                        if next_question is None:
                            next_question = Question.get(
                                pk=flow.next_question.pk).clone(
                                attrs={
                                    'qset': batch})
                            treated[next_question.identifier] = next_question
                            for option in flow.next_question.options.all():
                                # to do, appearantly clone question_opt not
                                # workng
                                QuestionOption.objects.create(
                                    question=next_question, order=option.order, text=option.text)
                    # first clone all flow parameters
                    args = flow.text_arguments
                    flow = flow.clone(
                        attrs={
                            'next_question': next_question,
                            'question': question})
                    for arg in args:
                        arg = arg.clone()
                        arg.flow = flow
                        arg.save()
                    flow.save()
            else:
                batch.start_question = start_question.clone(
                    attrs={'qset': batch})
                batch.save()
        return batch

# @job
# def refresh_loop_story(qset):
#     for


def next_inline_question(question, flows, answer_types=ALL_ANSWERS):
    if answer_types is None:
        answer_types = ALL_ANSWERS
    try:
        qflow = flows.get(question=question, validation__isnull=True)
        next_question = qflow.next_question
        if next_question and next_question.answer_type in answer_types:
            return next_question
        else:
            return next_inline_question(
                next_question, flows, answer_types=answer_types)
    except QuestionFlow.DoesNotExist:
        return None


def last_inline(question, flows):
    try:
        qflow = flows.get(
            question=question,
            validation__isnull=True,
            next_question__isnull=False)
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
            validation__isnull=True,
            next_question__isnull=False)
        return first_inline_flow_with_desc(iflow.next_question, desc)
    except QuestionFlow.DoesNotExist:
        return None


def inline_questions(question, flows):
    # to do, optimize this function
    # questions = [Question.get(pk=question.pk), ]
    questions = [question, ]
    try:
        qflow = flows.get(question=question, validation__isnull=True)
        questions.extend(inline_questions(qflow.next_question, flows))
    except QuestionFlow.DoesNotExist:
        pass
    return questions


def inline_flows(question, qflows):
    flows = []
    try:
        qflow = qflows.get(question=question, validation__isnull=True)
        flows.append(qflow)
        flows.extend(inline_questions(qflow.next_question, flows))
    except QuestionFlow.DoesNotExist:
        pass
    return flows


class QuestionSetChannel(CloneableMixin, BaseModel):
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
        #  previous question must be numeric
        return NumericalAnswer.objects.filter(
            interview=interview, question=self.value).last().value

    def odk_get_count(self, interview):
        raise Exception('need to do!')  # to do

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
    loop_starter = models.OneToOneField(Question, related_name='loop_started')
    repeat_logic = models.CharField(
        max_length=64,
        choices=REPEAT_OPTIONS,
        null=True,
        blank=True)
    loop_ender = models.OneToOneField(Question, related_name='loop_ended')
    loop_prompt = models.CharField(max_length=50, null=True, blank=True)

    def loop_questions(self):
        questions = self.loop_starter.qset.inlines_between(self.loop_starter, self.loop_ender)
        questions.add(self.loop_ender)
        return questions

    def save(self, *args, **kwargs):
        invalidate_obj(self.loop_starter)
        invalidate_obj(self.loop_ender)
        return super(QuestionLoop, self).save(*args, **kwargs)
