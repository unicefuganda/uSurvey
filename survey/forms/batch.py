from django import forms
from survey.models_file import *
from django.forms import ModelForm
from django.core.validators import *

class BatchForm(ModelForm):
    class Meta:
        model = Batch
        fields =['name','description']

    def clean_name(self):
        if len(Batch.objects.filter(name=self.cleaned_data['name'])) > 0:
            raise ValidationError('Batch with the same name already exist')
        return self.cleaned_data['name']
