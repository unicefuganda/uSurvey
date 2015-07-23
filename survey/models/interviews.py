import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from survey.models.interviewer import Interviewer
from survey.models.access_channels import InterviewerAccess
from survey.models.base import BaseModel
from rapidsms.contrib.locations.models import Point


def reply_test(cls, func):
    func.is_reply_test = True
    return func
 
class Interview(BaseModel):
    interviewer = models.ForeignKey(Interviewer, null=True, related_name="%(class)s")
    householdmember = models.ForeignKey("HouseholdMember", null=True, related_name="%(class)s")
    batch = models.ForeignKey("Batch", related_name='interviews')
    interview_channel = models.ForeignKey(InterviewerAccess, related_name='interviews')
    closure_date = models.DateTimeField(null=True, blank=True, editable=False)
    last_question = models.ForeignKey("Question", related_name='ongoing')
     
    def start(self):
        return self.batch.start_question
     
    def get_next_question(self, response):
        #get last question
        try:
            answer_class = str_to_class(self.last_question.answer_type)
            answer = answer_class(self.last_question, response)
            answer.interview = self
            answer.save()
            possible_replies = self.last_question.get_children()
            for question in possible_replies:
                if question.validation_test is None:
                    response = question
                elif getattr(Answer, question.validation_test)(answer.value, *question.test_arguments) == True:
                    response = question
                    break
            self.last_question = reponse
            self.save()
            return response 
        except:
            raise
     
    def respond(self, msg=None):
        if self.last_question is None:
            return self.start()
        else:
            return self.get_next_question(msg)
         
 
class Answer(BaseModel):
    interview = models.ForeignKey(Interview, related_name='%(class)s')
    question = models.OneToOneField("Question", null=True, related_name="%(class)s")
     
    @classmethod
    def answer_types(cls):
        return [cl._meta.verbose_name.title() for cl in Answer.__subclasses__()]
 

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
     
    def __init__(self, question, answer, *args, **kwargs):
        super(NumericalAnswer, self).__init__(self)
        try:
            self.value = int(answer)
        except Exception: raise
        self.question = question
 
 
class ODKGeoPoint(Point):
    altitude = models.DecimalField(decimal_places=3, max_digits=10)
    precision = models.DecimalField(decimal_places=3, max_digits=10)
 
    class Meta:
        app_label = 'survey'
 
class TextAnswer(Answer):
    value = models.CharField(max_length=100, blank=False, null=False)
 
    def __init__(self, question, answer, *args, **kwargs):
        super(TextAnswer, self).__init__(self)
        self.value = answer
        self.question = question
 
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
     
    def __init__(self, question, answer, *args, **kwargs):
        super(MultiChoiceAnswer, self).__init__(self)
        if isinstance(answer, basestring):
            self.value = question.options.get(text=answer)
        else: self.value = answer
        self.question = question
         
     
    @classmethod
    def validators(cls):
        return [cls.equals, ]
     
#     @classmethod
#     def equals(cls, answer, txt):
#         return answer.text.lower() == txt.lower() 
 
class MultiSelectAnswer(Answer):
    value = models.ManyToManyField("QuestionOption", null=True)
     
    def __init__(self, question, answer, *args, **kwargs):
        super(MultiSelectAnswer, self).__init__(self)
        self.value = answer
        self.question = question
 
    @classmethod
    def validators(cls):
        return [cls.equals, cls.contains]
 
    @classmethod
    def equals(cls, answer, txt):
        return answer.text.lower() == txt.lower()
 
class DateAnswer(Answer):
    value = models.DateField(null=True)
 
    def __init__(self, question, answer, *args, **kwargs):
        super(DateAnswer, self).__init__(self)
        self.value = answer
        self.question = question
 
    @classmethod
    def validators(cls):
        return [cls.greater_than, cls.equals, cls.less_than, cls.between]
 
class AudioAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)
     
    def __init__(self, question, answer, *args, **kwargs):
        super(AudioAnswer, self).__init__(self)
        self.value = answer
        self.question = question
    
    @classmethod
    def validators(cls):
        return []
 
class VideoAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)
     
    def __init__(self, question, answer, *args, **kwargs):
        super(VideoAnswer, self).__init__(self)
        self.value = answer
        self.question = question

    @classmethod
    def validators(cls):
        return []
 
class ImageAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)
     
    def __init__(self, question, answer, *args, **kwargs):
        super(ImageAnswer, self).__init__(self)
        self.value = answer
        self.question = question
 
    @classmethod
    def validators(cls):
        return []
 
class GeopointAnswer(Answer):
    value = models.ForeignKey(ODKGeoPoint, null=True)
     
    def __init__(self, question, answer, *args, **kwargs):
        super(GeopointAnswer, self).__init__(self)
        self.value = answer
        self.question = question
     
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
        unique_together = ('answer_type', 'channel')