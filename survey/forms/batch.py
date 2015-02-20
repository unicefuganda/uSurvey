from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models import BatchQuestionOrder
from survey.models.batch import Batch
from django.utils.safestring import mark_safe

from survey.models.formula import *

class TableMultiSelect(forms.SelectMultiple):

    class Media:
        css = ('css/tablemultiselect.css',)
        js = ('js/tablemultiselect.js', )    

    def render(self, name, value, attrs=None, choices=()):
        if attrs is None: attrs = {}
        questions = Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP')
        question_dict = {int(q.pk): [q.identifier, q.text, q.answer_type.upper()] for q in questions}
        html = super(TableMultiSelect, self).render(name, value, attrs, choices) + """
               <script type="text/javascript">
                   var qu_dict = """ + str(question_dict) + """;
                </script>"""
        return mark_safe(html)


class BatchForm(ModelForm):

    class Meta:
        model = Batch
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50})
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        existing_batches = Batch.objects.filter(name=name, survey=self.instance.survey)
        if existing_batches.count() > 0 and self.initial.get('name', None) != str(name):
            raise ValidationError('Batch with the same name already exists.')
        return self.cleaned_data['name']


class BatchQuestionsForm(ModelForm):
    questions = forms.ModelMultipleChoiceField(label=u'', queryset=Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP'),
                                               widget=TableMultiSelect(attrs={'class': 'multi-select'}))

    class Meta:
        model = Batch
        fields = ['questions']

    def __init__(self, batch=None, *args, **kwargs):
        super(BatchQuestionsForm, self).__init__(*args, **kwargs)
        self.fields['questions'].queryset = Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP').exclude(batches=batch)

    def save_question_to_batch(self, batch):
        for question in self.cleaned_data['questions']:
            question.save()
            order = BatchQuestionOrder.next_question_order_for(batch)
            BatchQuestionOrder.objects.create(question=question, batch=batch, order=order)
            question.batches.add(batch)

    def save(self, commit=True, *args, **kwargs):
        batch = super(BatchQuestionsForm, self).save(commit=commit, *args, **kwargs)

        if commit:
            batch.save()
            self.save_question_to_batch(batch)

