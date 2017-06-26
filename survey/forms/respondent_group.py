from django import forms
from survey.forms.form_helper import FormOrderMixin
from survey.models import MultiChoiceAnswer
from survey.models import RespondentGroupCondition
from survey.models import TemplateOption
from survey.models import Answer
from survey.models import RespondentGroup
from survey.models import MultiSelectAnswer
from survey.models import ParameterTemplate
from validation import get_response_validation_form


class GroupForm(get_response_validation_form(ParameterTemplate)):

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        if self.data.get('test_question', []):
            options = TemplateOption.objects.filter(
                question__pk=self.data['test_question'])
            self.fields['options'].choices = [
                (opt.order, opt.text) for opt in options]

    class Meta:
        exclude = []
        model = RespondentGroup
        fields = ['name', 'description', ]
        widgets = {
            'description': forms.Textarea(attrs={"rows": 6, "cols": 30}),
        }

    def save(self, *args, **kwargs):
        group = super(GroupForm, self).save(*args, **kwargs)
        validation_test = self.cleaned_data.get('validation_test', None)
        test_question = self.cleaned_data.get('test_question', None)
        if validation_test and test_question:
            group_condition = group.group_conditions.create(
                validation_test=validation_test, test_question=test_question)
            if validation_test == 'between':
                group_condition.arguments.create(
                    position=0, param=self.cleaned_data['min'])
                group_condition.arguments.create(
                    position=1, param=self.cleaned_data['max'])
            else:
                group_condition.arguments.create(
                    position=0, param=self.cleaned_data['value'])
        return group

