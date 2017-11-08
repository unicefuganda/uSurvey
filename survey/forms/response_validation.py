from django import forms
from survey.forms.form_helper import FormOrderMixin
from survey.models import Answer
from survey.models import ResponseValidation, TextArgument


class ResponseValidationForm(forms.ModelForm, FormOrderMixin):
    min = forms.CharField(required=False, max_length=50)
    max = forms.CharField(required=False, max_length=50)
    value = forms.CharField(required=False, max_length=50)
    CHOICES = [('', '----------Select Operator----------')]
    CHOICES.extend(ResponseValidation.VALIDATION_TESTS)
    validation_test = forms.ChoiceField(choices=CHOICES, label='Operator', required=True)

    def __init__(self, *args, **kwargs):
        super(ResponseValidationForm, self).__init__(*args, **kwargs)
        self.fields['value'].widget.attrs['class'] = 'expected-response'
        self.fields['min'].widget.attrs['class'] = 'expected-response'
        self.fields['max'].widget.attrs['class'] = 'expected-response'
        self.order_fields(['validation_test',
                           'value',
                           'min',
                           'max'])

    class Meta:
        exclude = []
        model = ResponseValidation
        widgets = {
            'description': forms.Textarea(attrs={"rows": 6, "cols": 30}),
        }

    def clean(self):
        validation_test = self.cleaned_data.get('validation_test', None)
        answer_type = self.cleaned_data.get('answer_type', None)
        try:
            method = getattr(Answer, validation_test, None)
        except Exception as e:
            method = None
            pass
        if method is None:
            raise forms.ValidationError('unsupported validator defined on test question')
        if validation_test == 'between':
            if self.cleaned_data.get('min', False) is False or self.cleaned_data.get('max', False) is False:
                raise forms.ValidationError('min and max values required for between condition')
        elif self.cleaned_data.get('value', False) is False:
            raise forms.ValidationError('Value is required for %s' % validation_test)
        return self.cleaned_data

    def save(self, *args, **kwargs):
        response_validation = super(ResponseValidationForm, self).save(*args, **kwargs)
        validation_test = self.cleaned_data.get('validation_test', None)
        if validation_test == 'between':
            TextArgument.objects.create(validation=response_validation, position=0, param=self.cleaned_data['min'])
            TextArgument.objects.create(validation=response_validation, position=1, param=self.cleaned_data['max'])
        else:
            TextArgument.objects.create(validation=response_validation, position=0, param=self.cleaned_data['value'])
        return response_validation
