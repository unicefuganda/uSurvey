from django import forms
from django.forms import ModelForm
import re
from survey.models import QuestionModule
from survey.models.batch import Batch
from survey.models import QuestionTemplate
from survey.models import HouseholdMemberGroup


class QuestionTemplateForm(ModelForm):
    
    class Meta:
        model = QuestionTemplate
        MODULE_CHOICES = [(module.id, module.name) for module in QuestionModule.objects.all()]
        HOUSEHOLD_GROUP_CHOICES = [(group.id, group.name) for group in HouseholdMemberGroup.objects.all()]
        widgets ={
            'text': forms.Textarea(attrs={"rows":4, "cols":100,"maxlength":"150"}),
            'module': forms.Select(choices=MODULE_CHOICES),
        }
