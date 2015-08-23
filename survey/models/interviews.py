import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from survey.models.interviewer import Interviewer
from survey.models.access_channels import InterviewerAccess
from survey.models.base import BaseModel
from rapidsms.contrib.locations.models import Point
from django import template


def reply_test(cls, func):
    func.is_reply_test = True
    return func
 
class Interview(BaseModel):
    interviewer = models.ForeignKey(Interviewer, null=True, related_name="interviews")
    householdmember = models.ForeignKey("HouseholdMember", null=True, related_name="interviews")
    batch = models.ForeignKey("Batch", related_name='interviews')
    interview_channel = models.ForeignKey(InterviewerAccess, related_name='interviews')
    closure_date = models.DateTimeField(null=True, blank=True, editable=False)
    last_question = models.ForeignKey("Question", related_name='ongoing', null=True, blank=True)
     
    def start(self):
        return self.batch.start_question
     
    def respond(self, reply=None):
        #get last question
        try:
            next_question = None
            if self.last_question is None:
                next_question = self.batch.start_question
            if reply is None: #if we are not replying, simply return last question or first question
                next_question = self.last_question or next_question
            else:
                flows = self.last_question.flows.all()
                resulting_flow = None
                last_resort = None
                for flow in flows:
                    if flow.validation_test:
                        if getattr(Answer, flow.validation_test)(reply, *flow.test_arguments) == True:
                            resulting_flow = flow
                            break
                    else:
                        last_resort = flow
                resulting_flow = resulting_flow or last_resort
                if resulting_flow:
                    answer_class = Answer.get_class(self.last_question.answer_type)
                    answer = answer_class(resulting_flow, reply)
                    answer.interview = self
                    answer.save()
                    next_question = resulting_flow.next_question
            if next_question:
                self.last_question = next_question
                self.save()
                question_context = template.Context(dict([(field.verbose_name.upper().replace(' ', '_'), 
                                                                getattr(self.householdmember, field.name))         
                                                                        for field in self.householdmember._meta.fields]))
                response_text =  template.Template(next_question.text).render(question_context)
                print 'response text is: ', response_text
                return response_text
        except:
            raise
    
    @classmethod 
    def pending_batches(cls, house_member, ea, survey):
        available_batches = ea.open_batches(survey, house_member)
        print 'available batches: ', available_batches
        completed_interviews = Interview.objects.filter(householdmember=house_member, batch__in=available_batches, 
                                                        closure_date__isnull=False)
        completed_batches = [interview.batch for interview in completed_interviews]
        return [batch for batch in available_batches if batch not in completed_batches]  
    
    @classmethod
    def interviews(cls, house_member, interviewer, survey):
        available_batches = ea.open_batches(survey, house_member)
        interviews = Interview.objects.filter(householdmember=house_member, batch__in=available_batches)
        #return (completed_interviews, pending_interviews)
        return (interviews.filter(closure_date__isnull=False), interviews.filter(closure_date__isnull=True))
#         completed_batches = [interview.batch for interview in completed_interviews]
#         return [batch for batch in available_batches if batch not in completed_batches]

    def members_with_open_batches(self):
        pass
        
    
#     @property
#     def first_question(self):
#         question = self.batch.start_question
        
    class Meta:
        app_label = 'survey'
        unique_together = [('householdmember', 'batch'), ]
    
class Answer(BaseModel):
    interview = models.ForeignKey(Interview, related_name='%(class)s')
#     interviewer_response = models.CharField(max_length=200)  #This shall hold the actual response from interviewer
#                                                             #value shall hold the exact worth of the response
    flow = models.OneToOneField("QuestionFlow", null=True, related_name="%(class)s")
     
    @classmethod
    def answer_types(cls):
        return [cl._meta.verbose_name.title() for cl in Answer.__subclasses__()]
    
    @classmethod
    def get_class(cls, verbose_name):
        verbose_name = verbose_name.strip()
        for cl in Answer.__subclasses__():
            if cl._meta.verbose_name.title() == verbose_name:
                return cl
        ValueError('unknown class')

    @classmethod
    def contains(cls, answer, txt):
        answer = answer.lower()
        txt = txt.lower()
        try:
            return answer.index(txt) >= 0
        except ValueError:
            return False
 

    @classmethod
    def equals(cls, answer, value):
        return answer == value
 

    @classmethod
    def starts_with(cls, answer, txt):
        answer = answer.lower()
        txt = txt.lower()
        return answer.startswith(txt)
 

    @classmethod
    def ends_with(cls, answer, txt):
        answer = answer.lower()
        txt = txt.lower()
        return answer.endswith(txt)
 

    @classmethod
    def greater_than(cls, answer, value):
        return answer > value
     

    @classmethod
    def less_than(cls, answer, value):
        return answer < value
     

    @classmethod
    def between(cls, answer, lowerlmt, upperlmt):
        return upperlmt > answer >= lowerlmt
     

    @classmethod
    def passes_test(cls, text_exp):
        return bool(eval(text_exp))
 
    @classmethod
    def validators(cls):
        return [cls.starts_with, cls.ends_with, cls.equals, cls.between, cls.less_than, 
                cls.greater_than, cls.contains, ]
         
    class Meta:
        app_label = 'survey'
        abstract = True
        get_latest_by = 'created'
  
class NumericalAnswer(Answer):
    value = models.PositiveIntegerField(max_length=5, null=True) 
     
    @classmethod
    def validators(cls):
        return [cls.greater_than, cls.equals, cls.less_than, cls.between]
     
    def __init__(self, flow, answer, *args, **kwargs):
        super(NumericalAnswer, self).__init__()
        try:
            self.value = int(answer)
        except Exception: raise
        self.flow = flow 
 
class ODKGeoPoint(Point):
    altitude = models.DecimalField(decimal_places=3, max_digits=10)
    precision = models.DecimalField(decimal_places=3, max_digits=10)
 
    class Meta:
        app_label = 'survey'
 
class TextAnswer(Answer):
    value = models.CharField(max_length=100, blank=False, null=False)
 
    def __init__(self, flow, answer, *args, **kwargs):
        super(TextAnswer, self).__init__()
        self.value = answer
        self.flow = flow
 
    @classmethod
    def validators(cls):
        return [cls.starts_with, cls.equals, cls.ends_with, cls.contains]
 
    @classmethod
    def equals(cls, answer, value):
        answer = answer.lower()
        value = value.lower()
        return answer == value
 
class MultiChoiceAnswer(Answer):
    value = models.ForeignKey("QuestionOption", null=True)
     
    def __init__(self, flow, answer, *args, **kwargs):
        super(MultiChoiceAnswer, self).__init__()
        if isinstance(answer, basestring):
            self.value = flow.question.options.get(text=answer)
        else: self.value = answer
        self.flow = flow
              
    @classmethod
    def validators(cls):
        return [cls.equals, ]
     
#     @classmethod
#     def equals(cls, answer, txt):
#         return answer.text.lower() == txt.lower() 
 
class MultiSelectAnswer(Answer):
    value = models.ManyToManyField("QuestionOption", null=True)
     
    def __init__(self, flow, answer, *args, **kwargs):
        super(MultiSelectAnswer, self).__init__()
        self.value = answer
        self.flow = flow
 
    @classmethod
    def validators(cls):
        return [cls.equals, cls.contains]
 
    @classmethod
    def equals(cls, answer, txt):
        return answer.text.lower() == txt.lower()
 
class DateAnswer(Answer):
    value = models.DateField(null=True)
 
    def __init__(self, flow, answer, *args, **kwargs):
        super(DateAnswer, self).__init__()
        self.value = answer
        self.flow = flow
 
    @classmethod
    def validators(cls):
        return [cls.greater_than, cls.equals, cls.less_than, cls.between]
 
class AudioAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)
     
    def __init__(self, flow, answer, *args, **kwargs):
        super(AudioAnswer, self).__init__()
        self.value = answer
        self.flow = flow
    
    @classmethod
    def validators(cls):
        return []
 
class VideoAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)
     
    def __init__(self, flow, answer, *args, **kwargs):
        super(VideoAnswer, self).__init__()
        self.value = answer
        self.flow = flow

    @classmethod
    def validators(cls):
        return []
 
class ImageAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)
     
    def __init__(self, flow, answer, *args, **kwargs):
        super(ImageAnswer, self).__init__()
        self.value = answer
        self.flow = flow
 
    @classmethod
    def validators(cls):
        return []
 
class GeopointAnswer(Answer):
    value = models.ForeignKey(ODKGeoPoint, null=True)
     
    def __init__(self, flow, answer, *args, **kwargs):
        super(GeopointAnswer, self).__init__()
        self.value = answer
        self.flow = flow
     
    @classmethod
    def validators(cls):
        return [cls.equals]    

class AnswerAccessDefinition(BaseModel):
    ACCESS_CHANNELS = [(name, name) for name in InterviewerAccess.access_channels()]
    ANSWER_TYPES = [(name, name) for name in Answer.answer_types()]
    answer_type = models.CharField(max_length=100, choices=ANSWER_TYPES)
    channel = models.CharField(max_length=100, choices=ACCESS_CHANNELS)
            
    class Meta:
        app_label = 'survey'
        unique_together = [('answer_type', 'channel'), ]
        
# class 