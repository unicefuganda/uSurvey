from django import forms
from django.forms import ModelForm
from survey.models import Batch, BatchChannel, QuestionTemplate, WebAccess


class BatchForm(ModelForm):
    access_channels = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(attrs={'class': 'access_channels'}),
                                                choices=[opt for opt in BatchChannel.ACCESS_CHANNELS
                                                         if not opt[0] == WebAccess.choice_name()])

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            initial = kwargs.setdefault('initial', {})
            initial['access_channels'] = [
                c.channel for c in kwargs['instance'].access_channels.all()]
        forms.ModelForm.__init__(self, *args, **kwargs)

    class Meta:
        model = Batch
        fields = ['name', 'description', 'survey', ]

        widgets = {
            'description': forms.Textarea(attrs={"rows": 3, "cols": 60}),
            'survey': forms.HiddenInput(),
        }

    def save(self, commit=True, **kwargs):
        batch = super(BatchForm, self).save(commit=commit)
        bc = BatchChannel.objects.filter(batch=batch)
        bc.delete()
        for val in kwargs['access_channels']:
            BatchChannel.objects.create(batch=batch, channel=val)


class BatchQuestionsForm(ModelForm):
    questions = forms.ModelMultipleChoiceField(label=u'', queryset=QuestionTemplate.objects.filter(),
                                               widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))

    class Meta:
        model = Batch
        fields = []

    def __init__(self, batch=None, *args, **kwargs):
        super(BatchQuestionsForm, self).__init__(*args, **kwargs)

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
