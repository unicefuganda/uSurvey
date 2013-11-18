from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models import Formula


class FormulaForm(ModelForm):

    def __init__(self, indicator=None, *args, **kwargs):
        super(FormulaForm, self).__init__(*args, **kwargs)

        self.indicator = indicator

        question_choices = []
        if indicator.batch:
            for question in indicator.batch.all_questions():
                if question.module == indicator.module:
                    question_choices.append((question.id, question.text))

            self.fields['numerator'].choices = question_choices
            self.fields['denominator'].choices = question_choices
            self.fields['count'].choices = question_choices

        if indicator:
            self.delete_fields_based_on(indicator)

    def delete_fields_based_on(self, indicator):
        if indicator.is_percentage_indicator():
            deleted_fields = ['count']
        else:
            deleted_fields = ['numerator', 'denominator']

        for field in deleted_fields:
            del self.fields[field]

    def clean(self):
        cleaned_data = self.cleaned_data

        error_message = 'Formula already exist for indicator %s.' % self.indicator.name
        existing_formula = []
        if self.indicator and self.indicator.is_percentage_indicator():
            existing_formula = Formula.objects.filter(indicator=self.indicator, numerator=cleaned_data['numerator'],
                                                      denominator=cleaned_data['denominator'])

        if self.indicator and not self.indicator.is_percentage_indicator():
            existing_formula = Formula.objects.filter(indicator=self.indicator, count=cleaned_data['count'])

        if existing_formula:
            raise ValidationError(error_message)

        return cleaned_data

    class Meta:
        model = Formula
        fields = ['numerator', 'denominator', 'count']