from django import forms
from django.forms import ModelForm
from survey.models.batch import Batch

from survey.models.formula import *


class BatchForm(ModelForm):
    class Meta:
        model = Batch
        fields =['name','description']
        widgets={
            'description':forms.Textarea(attrs={"rows":4, "cols":50})
        }

    def clean_name(self):
        if len(Batch.objects.filter(name=self.cleaned_data['name'])) > 0:
            raise ValidationError('Batch with the same name already exist')
        return self.cleaned_data['name']


class BatchQuestionsForm(ModelForm):
    questions = forms.ModelMultipleChoiceField(label=u'', queryset=Question.objects.all(),
                                                widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))

    class Meta:
        model = Batch
        fields = ['questions' ]

