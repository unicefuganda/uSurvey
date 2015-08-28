from django.db import models
from survey.models.interviewer import Interviewer
from survey.models.base import BaseModel
from survey.models.batch import Batch

class HouseholdMemberBatchCompletion(BaseModel):
    householdmember = models.ForeignKey('HouseholdMember', null=True, related_name="completed_member_batches")
    batch = models.ForeignKey(Batch, null=True, related_name="completed_households")
    interviewer = models.ForeignKey(Interviewer, null=True, related_name="completed_batches")

class HouseholdBatchCompletion(BaseModel):
    household = models.ForeignKey('Household', null=True, related_name="batch_completion_batches")
    batch = models.ForeignKey(Batch, null=True, related_name="batch_completion_households")
    interviewer = models.ForeignKey(Interviewer, null=True, related_name="batch_completed_households")
    
class HouseMemberSurveyCompletion(BaseModel):
    householdmember = models.ForeignKey('HouseholdMember', null=True, related_name="completion_register")
    survey = models.ForeignKey('Survey', related_name='completion_register')
    interviewer = models.ForeignKey(Interviewer, null=True, related_name="house_member_completion")
    
class HouseSurveyCompletion(BaseModel):
    household = models.ForeignKey('Household', null=True, related_name="completion_registry")
    survey = models.ForeignKey('Survey', related_name='house_completion')
    interviewer = models.ForeignKey(Interviewer, null=True, related_name="house_completion")