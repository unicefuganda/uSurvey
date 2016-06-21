from django.db import models
from django.db.models import Max
from survey.models.householdgroups import HouseholdMemberGroup
from survey.models.locations import Location
from survey.models.surveys import Survey
from survey.models.base import BaseModel
from survey.utils.views_helper import get_descendants
from survey.models.questions import Question, QuestionFlow
from survey.forms.logic import LogicForm
from survey.models.access_channels import InterviewerAccess
# from survey.models.enumeration_area import EnumerationArea
from survey.models.interviews import AnswerAccessDefinition, Answer
from survey.models.access_channels import ODKAccess
from django.core.exceptions import ValidationError
from ordered_set import OrderedSet
from collections import OrderedDict
from memoize import memoize
from django.conf import settings

ALL_GROUPS = HouseholdMemberGroup.objects.all()
ALL_ANSWERS = Answer.answer_types()
class Batch(BaseModel):
    order = models.PositiveIntegerField(null=True)
    name = models.CharField(max_length=100, blank=False, null=True,db_index=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    survey = models.ForeignKey(Survey, null=True, related_name="batches")
#     eas = models.ManyToManyField(EnumerationArea, related_name='batches', null=True) #enumeration areas for which this Batch is open
#     group = models.ForeignKey("HouseholdMemberGroup", null=True, related_name="question_group")
    start_question = models.OneToOneField(Question, related_name='starter_batch', null=True, blank=True, on_delete=models.SET_NULL)
    BATCH_IS_OPEN_MESSAGE = "Batch cannot be deleted because it is open in %s."
    BATCH_HAS_ANSWERS_MESSAGE = "Batch cannot be deleted because it has responses."

    class Meta:
        app_label = 'survey'
        unique_together = [('survey', 'name',) ]
        
    def save(self, *args, **kwargs):
        last_order = Batch.objects.aggregate(Max('order'))['order__max']
        self.order = last_order + 1 if last_order else 1
        super(Batch, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s" % self.name

    def can_be_deleted(self):
        return True, ''

    def get_looper_flow(self, question):
        try:
            return question.connecting_flows.get(desc=LogicForm.BACK_TO_ACTION)
        except QuestionFlow.DoesNotExist:
            return first_inline_flow_with_desc(question, LogicForm.BACK_TO_ACTION)

    def loop_starters(self):
        from survey.forms.logic import LogicForm
        flows = QuestionFlow.objects.filter(next_question__batch=self, desc=LogicForm.BACK_TO_ACTION)
        return set([f.next_question for f in flows])

    def loop_enders(self):
        from survey.forms.logic import LogicForm
        flows = QuestionFlow.objects.filter(question__batch=self, desc=LogicForm.BACK_TO_ACTION)
        return set([f.question for f in flows])

    def non_response_enabled(self, ea):
        locations = set()
        ea_locations = ea.locations.all()
        if ea_locations:
            map(lambda loc: locations.update(loc.get_ancestors(include_self=True)), ea_locations)
        return self.open_locations.filter(non_response=True, location__pk__in=[location.pk for location in locations]).exists()

    @property
    def answer_types(self):
        access_channels = self.access_channels.values_list('channel', flat=True)
        return set(AnswerAccessDefinition.objects.filter(channel__in=access_channels).values_list('answer_type', flat=True))
    
    def get_non_response_active_locations(self):
        locations = set()
        locations_register = self.open_locations.filter(non_response=True)
        if locations_register:
            map(lambda reg: locations.update(reg.location.get_descendants(include_self=True)), locations_register)
        return locations

    @property
    def non_response_eas(self):
        eas = set()
        locations = self.get_non_response_active_locations()
        map(lambda loc: eas.update(loc.enumeration_areas.all()), locations)
        return eas
    
    def other_surveys_with_open_batches_in(self, location):
        batch_ids = location.open_batches.all().exclude(batch__survey=self.survey).values_list('batch',flat=True)
        return Survey.objects.filter(batch__id__in = batch_ids)
    
    def open_for_location(self, location):
        return self.open_locations.get_or_create(batch=self, location=location)
    
    def close_for_location(self, location):
        self.open_locations.filter(batch=self, location=location).delete()
        
    def is_closed_for(self, location):
        #its closed if its closed in any parent loc or self
        locations = location.get_ancestors(include_self=True)
        return self.open_locations.filter(location__pk__in=locations).count() == 0

    def is_open_for(self, location):
        return not self.is_closed_for(location)
    
    def is_applicable(self, house_member):
        return True #probably might be used later

    def next_inline(self, question, groups=ALL_GROUPS, channel=ODKAccess.choice_name(), exclude_groups=[]):
        qflows = QuestionFlow.objects.filter(question__batch=self, validation_test__isnull=True)
        if qflows.exists():
            return next_inline_question(question, qflows, groups,
                                        AnswerAccessDefinition.answer_types(channel), exclude_groups)

    def is_open(self):
        return self.open_locations.all().exists()
    
    def last_question_inline(self):
        qflows = QuestionFlow.objects.filter(question__batch=self, validation_test__isnull=True)
        if qflows.exists():
            return last_inline(self.start_question, qflows)
        else:
            return self.start_question
        
    def questions_inline(self):
        qflows = QuestionFlow.objects.filter(question__batch=self, validation_test__isnull=True)
        if self.start_question:
            inlines = inline_questions(self.start_question, qflows)
            if inlines and inlines[-1] is None:
                inlines.pop(-1)
            return inlines
        else:
            return []

    @memoize(timeout=settings.MEMORIZE_TIMEOUT)
    def loop_backs_questions(self):
        '''
        :return: loop question structure for this batch (q_start_pk, q_end_pk) = []
        '''
        survey_questions = self.survey_questions
        loop_starters = self.loop_starters()
        loop_enders = self.loop_enders()
        start = None
        loop_desc = OrderedDict()
        present_loop = []
        for q in survey_questions:
            if q in loop_starters:
                start = q
                present_loop = []
            if q in loop_enders:
                present_loop.append(q)
                loop_desc[(start.pk, q.pk)] = present_loop
                start = None
            if start:
                present_loop.append(q)
        #just transpose
        return loop_desc

    @memoize(timeout=settings.MEMORIZE_TIMEOUT)
    def loop_back_boundaries(self):
        loop_desc = self.loop_backs_questions()
        quest_map = OrderedDict()
        for boundary, loop_questions in loop_desc.items():
            map(lambda q: quest_map.update({q.pk : boundary}), loop_questions)
        return quest_map

    def previous_inlines(self, question):
        inlines = self.questions_inline()
        if question not in inlines:
            raise ValidationError('%s not inline' % question.identifier)
        previous = []
        for q in inlines:
            if q.identifier == question.identifier:
                break
            else:
                previous.append(q)
        return set(previous)

        
    def zombie_questions(self):
        return Question.zombies(self)

    @property
    @memoize(timeout=settings.MEMORIZE_TIMEOUT)
    def survey_questions(self):
        inline_ques = self.questions_inline()
        questions = OrderedSet(inline_ques)
        survey_questions = OrderedSet()
        for ques in inline_ques:
            survey_questions.append(ques)
            map(lambda q: survey_questions.add(q), ques.direct_sub_questions()) #boldly assuming subquests dont go
                                                                #more than quest subquestion deep for present implemnt
        return survey_questions

    def activate_non_response_for(self, location):
        self.open_locations.filter(location=location).update(non_response=True)

    def deactivate_non_response_for(self, location):
        self.open_locations.filter(location=location).update(non_response=False)

# def sub_questions(question, flows):
#     questions = OrderedSet()
#     try:
#         qflows = flows.filter(question=question).exclude(next_question=question)
#         if qflows:
#             for flow in qflows:
#                 if flow.next_question:
#                     questions.add(flow.next_question)
#                     subsequent = sub_questions(flow.next_question, flows)
#                     map(lambda q: questions.add(q), subsequent)
#     except QuestionFlow.DoesNotExist:
#         return OrderedSet()
#     return questions


def next_inline_question(question, flows, groups=ALL_GROUPS, answer_types=ALL_ANSWERS, exclude_groups=[]):
    if groups is None:
        groups = ALL_GROUPS
    if answer_types is None:
        answer_types = ALL_ANSWERS
    try:
        qflow = flows.get(question=question, validation_test__isnull=True)
        next_question = qflow.next_question
        if next_question and next_question.group in groups and next_question.group not in exclude_groups and \
                                      next_question.answer_type in answer_types:
            return next_question
        else:
            return next_inline_question(next_question, flows, groups=groups, answer_types=answer_types,
                                        exclude_groups=exclude_groups)
    except QuestionFlow.DoesNotExist:
        return None


def last_inline(question, flows):
    try:
        qflow = flows.get(question=question, validation_test__isnull=True, next_question__isnull=False)
        return last_inline(qflow.next_question, flows)
    except QuestionFlow.DoesNotExist:
        return question


def first_inline_flow_with_desc(question, desc):
    try:
        if question.flows.filter(desc=desc).exists():
            return question.flows.get(desc=desc)
        if question.connecting_flows.filter(desc=desc).exists():
            return None
        iflow = question.flows.get(validation_test__isnull=True, next_question__isnull=False)
        return first_inline_flow_with_desc(iflow.next_question, desc)
    except QuestionFlow.DoesNotExist:
        return None

def inline_questions(question, flows):
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


#     @property
#     def batch_questions(self):
#         flows = self.flows.all()
#         questions = set([self.start_question, ])
#         for flow in flows:
#             questions.add(flow.next_question)
#         return questions

#     map(lambda flow: question_map.update({flow.next_question.identifier: flow.next_question}), flows)
#     compute()


class BatchLocationStatus(BaseModel):
    batch = models.ForeignKey(Batch, null=True, related_name="open_locations")
    location = models.ForeignKey(Location, null=True, related_name="open_batches")
    non_response = models.BooleanField(null=False, default=False)

class BatchChannel(BaseModel):
    ACCESS_CHANNELS = [(name, name) for name in InterviewerAccess.access_channels()]
    batch = models.ForeignKey(Batch, related_name='access_channels')
    channel = models.CharField(max_length=100, choices=ACCESS_CHANNELS)
    
    class Meta:
        app_label = 'survey'
        unique_together = ('batch', 'channel')