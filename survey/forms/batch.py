from django import forms
from django.forms import ModelForm
from survey.models.batch import Batch

from survey.models.formula import *


class BatchForm(ModelForm):

    class Meta:
        model = Batch
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50})
        }

    def clean_name(self):
        if self.instance and self.instance.survey and Batch.objects.filter(name=self.cleaned_data['name'],
                                                                           survey=self.instance.survey).count() > 0:
            raise ValidationError('Batch with the same name already exists.')
        return self.cleaned_data['name']


class BatchQuestionsForm(ModelForm):
    questions = forms.ModelMultipleChoiceField(label=u'', queryset=Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP'),
                                               widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))

    class Meta:
        model = Batch
        fields = ['questions']

    def __init__(self, *args, **kwargs):
        super(BatchQuestionsForm, self).__init__(*args, **kwargs)
        self.fields['questions'].queryset = Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP')

    def save_question_to_batch(self, batch):
        for question in self.cleaned_data['questions']:
            question.save()
            question.batches.add(batch)

    def save(self, commit=True, *args, **kwargs):
        batch = super(BatchQuestionsForm, self).save(commit=commit, *args, **kwargs)

        if commit:
            batch.save()
            self.save_question_to_batch(batch)