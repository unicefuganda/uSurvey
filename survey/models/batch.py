from django.db import models
from django.db.models import Max
from survey.models.locations import Location
from survey.models.surveys import Survey
from survey.models.base import BaseModel
from survey.utils.views_helper import get_descendants
from survey.models.questions import Question, QuestionFlow
from survey.models.access_channels import InterviewerAccess
# from survey.models.enumeration_area import EnumerationArea
from survey.models.interviews import AnswerAccessDefinition
from survey.models.access_channels import ODKAccess


class Batch(BaseModel):
    order = models.PositiveIntegerField(max_length=2, null=True)
    name = models.CharField(max_length=100, blank=False, null=True)
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

    @property
    def answer_types(self):
        access_channels = self.access_channels.values_list('channel', flat=True)
        return set(AnswerAccessDefinition.objects.filter(channel__in=access_channels).values_list('answer_type', flat=True))
    
    def get_non_response_active_locations(self):
        non_response_active_batch_location_status = self.open_locations.filter(non_response=True)
        locations = []
        map(lambda batch_status: locations.append(batch_status.location), non_response_active_batch_location_status)
        return locations
    
    def other_surveys_with_open_batches_in(self, location):
        batch_ids = location.open_batches.all().exclude(batch__survey=self.survey).values_list('batch',flat=True)
        return Survey.objects.filter(batch__id__in = batch_ids)
    
    def open_for_location(self, location):
        all_related_locations = location.get_descendants(True)
        for related_location in all_related_locations:
            self.open_locations.get_or_create(batch=self, location=related_location)
        return self.open_locations.get_or_create(batch=self, location=location)
    
    def close_for_location(self, location):
        self.open_locations.filter(batch=self).delete()
        
    def is_closed_for(self, location):
        return self.open_locations.filter(location=location).count() == 0

    def is_open_for(self, location):
        return not self.is_closed_for(location)
    
    def is_applicable(self, house_member):
        return True #probably might be used later

    def next_inline(self, question, groups=None, channel=ODKAccess.choice_name()):
        qflows = QuestionFlow.objects.filter(question__batch=self, validation_test__isnull=True)
        if qflows.exists():
            return next_inline_question(question, qflows, groups, AnswerAccessDefinition.answer_types(channel))

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
            return inline_questions(self.start_question, qflows)
        else:
            return []
        
    def zombie_questions(self):
        return Question.zombies(self)


def next_inline_question(question, flows, groups=None, answer_types=[]):
    try:
        qflow = flows.get(question=question, validation_test__isnull=True)
        next_question = qflow.next_question
        if groups is None or (next_question.group in groups and next_question.anwser_type in answer_types):
            return next_question
        else:
            return next_inline_question(next_question, flows, groups)
    except QuestionFlow.DoesNotExist:
        return None


def last_inline(question, flows):
    try:
        qflow = flows.get(question=question, validation_test__isnull=True)
        return last_inline(qflow.next_question, flows)
    except QuestionFlow.DoesNotExist:
        return question


def inline_questions(question, flows):
    questions = [question, ]
    try:
        qflow = flows.get(question=question, validation_test__isnull=True)
        questions.extend(inline_questions(qflow.next_question, flows))
    except QuestionFlow.DoesNotExist:
        pass
    return questions
    
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