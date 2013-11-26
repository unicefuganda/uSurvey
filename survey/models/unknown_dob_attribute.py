from survey.models import BaseModel
from django.db import models
from survey.models.households import HouseholdMember


class UnknownDOBAttribute(BaseModel):
    UNKNOWN_ATTRIBUTE_TYPES = {
        ('MONTH', 'MONTH'),
        ('YEAR', 'YEAR')}

    household_member = models.ForeignKey(HouseholdMember, related_name='unknown_dob_attribute')
    type = models.CharField(max_length=15, blank=False, null=False, choices=UNKNOWN_ATTRIBUTE_TYPES)

