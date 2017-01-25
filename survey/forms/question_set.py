from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models import QuestionSet, QuestionTemplate, WebAccess, QuestionSetChannel
from survey.models import Batch
from django.utils.safestring import mark_safe
from survey.models.formula import *


def get_question_set_form(model_class):

    class QuestionSetForm(ModelForm):
        access_channels = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(attrs={'class': 'access_channels'}),
                                                    choices=[opt for opt in QuestionSetChannel.ACCESS_CHANNELS
                                                             if not opt[0] == WebAccess.choice_name()])

        def __init__(self, *args, **kwargs):
            if kwargs.get('instance'):
                initial = kwargs.setdefault('initial', {})
                initial['access_channels'] = [
                    c.channel for c in kwargs['instance'].access_channels.all()]
            super(QuestionSetForm, self).__init__(*args, **kwargs)
            # import pdb; pdb.set_trace()


        class Meta:
            model = model_class
            fields = ['name', 'description', ]

            widgets = {
                'description': forms.Textarea(attrs={"rows": 4, "cols": 30}),
            }

        def clean_name(self):
            name = self.cleaned_data['name'].strip()
            if self.instance is None and model_class.objects.filter(name=name).exists():
                raise ValidationError('Name already exists')
            return name

        def save(self, commit=True, **kwargs):
            question_set = super(QuestionSetForm, self).save(commit=commit)
            bc = QuestionSetChannel.objects.filter(qset=question_set)
            bc.delete()
            for val in kwargs['access_channels']:
                QuestionSetChannel.objects.create(qset=question_set, channel=val)
            return question_set
    return QuestionSetForm


class BatchForm(get_question_set_form(Batch)):
    class Meta:
        model = Batch
        fields = ['name', 'description', 'survey', ]

        widgets = {
            'description': forms.Textarea(attrs={"rows": 4, "cols": 40}),
            'survey': forms.HiddenInput(),
        }

#
# class BatchQuestionsForm(ModelForm):
#     questions = forms.ModelMultipleChoiceField(label=u'', queryset=QuestionTemplate.objects.filter(),
#                                                widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))
#
#     class Meta:
#         model = Batch
#         fields = []
#
#     def __init__(self, batch=None, *args, **kwargs):
#         super(BatchQuestionsForm, self).__init__(*args, **kwargs)

#     def save_question_to_batch(self, batch):
#         for question in self.cleaned_data['questions']:
#             question.save()
#             order = BatchQuestionOrder.next_question_order_for(batch)
#             BatchQuestionOrder.objects.create(question=question, batch=batch, order=order)
#             question.batches.add(batch)
#
#     def save(self, commit=True, *args, **kwargs):
#         batch = super(BatchQuestionsForm, self).save(commit=commit, *args, **kwargs)
#
#         if commit:
#             batch.save()
#             self.save_question_to_batch(batch)
