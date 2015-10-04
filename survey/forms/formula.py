from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from survey.models import Formula, HouseholdMemberGroup


class FormulaForm(ModelForm):
    OPTIONS = (
                ("GROUP", "GROUP"),
                ("QUESTION", "QUESTION"),
    )

    def __init__(self, indicator=None, *args, **kwargs):
        super(FormulaForm, self).__init__(*args, **kwargs)
        self.indicator = indicator
        self.fields['denominator'].label = ""
        self.fields['count'].label = ""
        self.fields['groups'].label = ""

        question_choices = []
        if indicator.batch:
            for question in indicator.batch.survey_questions:
                if question.module == indicator.module:
                    question_choices.append((question.id, question.text))

            groups = HouseholdMemberGroup.objects.all().exclude(name='REGISTRATION GROUP')
            self.fields['numerator'].choices = question_choices
            self.fields['denominator'].choices = question_choices
            self.fields['count'].choices = question_choices
            self.fields['groups'].choices = [(group.id, group.name) for group in groups]

        if indicator:
            self.delete_fields_based_on(indicator)

    def delete_fields_based_on(self, indicator):
        if indicator.is_percentage_indicator():
            deleted_fields = ['count']
            denominator_label = "Denominator"
        else:
            deleted_fields = ['numerator', 'denominator', 'numerator_options']
            denominator_label = "Count"

        for field in deleted_fields:
            del self.fields[field]
        self.fields['denominator_type'].label = denominator_label

    def clean(self):
        cleaned_data = self.cleaned_data
        is_question_selected = cleaned_data['denominator_type'] == 'QUESTION'
        denominator = cleaned_data.get('denominator', None)
        groups = cleaned_data.get('groups', None)
        count = cleaned_data.get('count', None)

        error_message = 'Formula already exist for indicator %s.' % self.indicator.name
        existing_formula = []

        if self.indicator and self.indicator.is_percentage_indicator():

            if denominator:
                existing_formula = Formula.objects.filter(indicator=self.indicator, numerator=cleaned_data['numerator'],
                                                          denominator=denominator)
            if groups and not is_question_selected:
                existing_formula = Formula.objects.filter(indicator=self.indicator, numerator=cleaned_data['numerator'],
                                                          groups=groups)

        if self.indicator and not self.indicator.is_percentage_indicator():
            if count:
                existing_formula = Formula.objects.filter(indicator=self.indicator, count=count)

            if groups and not is_question_selected:
                existing_formula = Formula.objects.filter(indicator=self.indicator, groups=groups)

        if existing_formula:
            raise ValidationError(error_message)

        return self.cleaned_data

    class Meta:
        model = Formula
        fields = ['numerator', 'numerator_options', 'denominator_type', 'groups', 'denominator', 'count',
                  'denominator_options']

    denominator_type = forms.CharField(label="Denominator", widget=forms.Select(choices=OPTIONS))