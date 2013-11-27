from django.db import models

from survey.models.investigator import Investigator
from survey.models.base import BaseModel
from survey.models.batch import Batch
from survey.models.households import Household, HouseholdMember


class HouseholdMemberBatchCompletion(BaseModel):
    household = models.ForeignKey(Household, null=True, related_name="completed_batches")
    householdmember = models.ForeignKey(HouseholdMember, null=True, related_name="completed_member_batches")
    batch = models.ForeignKey(Batch, null=True, related_name="completed_households")
    investigator = models.ForeignKey(Investigator, null=True, related_name="completed_batches")


class HouseholdBatchCompletion(BaseModel):
    household = models.ForeignKey(Household, null=True, related_name="batch_completion_batches")
    batch = models.ForeignKey(Batch, null=True, related_name="batch_completion_households")
    investigator = models.ForeignKey(Investigator, null=True, related_name="batch_completion_completed_households")