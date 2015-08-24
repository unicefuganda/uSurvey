import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from survey.models.interviews import Answer
from survey.models.householdgroups import HouseholdMemberGroup
from survey.models.base import BaseModel
from mptt.models import MPTTModel, TreeForeignKey
from model_utils.managers import InheritanceManager

class Question(BaseModel):
    ANSWER_TYPES = [(name, name) for name in Answer.answer_types()]
    identifier = models.CharField(max_length=100, blank=False, null=True, verbose_name='Variable Name')
    text = models.CharField(max_length=150, blank=False, null=False)
    answer_type = models.CharField(max_length=100, blank=False, null=False, choices=ANSWER_TYPES)
    group = models.ForeignKey(HouseholdMemberGroup, related_name='questions')
    batch = models.ForeignKey('Batch', related_name='batch_questions')
    module = models.ForeignKey("QuestionModule", null=True, related_name="questions")

    class Meta:
        app_label = 'survey'        
        unique_together = [('identifier', 'batch'), ]

    def __unicode__(self):
        return "%s - %s: (%s)" % (self.identifier, self.text, self.answer_type.upper())
    
class QuestionFlow(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__) for validator in Answer.validators()]
    question = models.ForeignKey(Question, related_name='flows')
    validation_test = models.CharField(max_length=200, null=True, blank=True, choices=VALIDATION_TESTS)    
    name = models.CharField(max_length=200, null=True, blank=True, unique=True) #if validation passes, classify this flow response as having this value  
    next_question = models.ForeignKey(Question, related_name='connecting_flows')
    
    class Meta:
        app_label = 'survey'        
        unique_together = [('question', 'next_question'),]
    
    @property
    def test_arguments(self):
        args = TestArgument.objects.filter(flow=self).select_subclasses()
        args = sorted(args, key=lambda arg: arg.position)
        return [arg.param for arg in args]

class TestArgument(models.Model):
    objects = InheritanceManager()
    flow = models.ForeignKey(QuestionFlow, related_name='"%(class)s"')
    position = models.PositiveIntegerField()
    
    @classmethod
    def argument_types(cls):
        return [cl.__name__ for cl in cls.__subclasses__()]
    
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
 
    class Meta:
        app_label = 'survey'
 
    def to_text(self):
        return "%d: %s" % (self.order, self.text)
