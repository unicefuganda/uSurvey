from django import forms
from survey.models import *
from django.forms import ModelForm
from django.core.validators import *

class BatchForm(ModelForm):
    class Meta:
        model = Batch
        fields =['name','description']
