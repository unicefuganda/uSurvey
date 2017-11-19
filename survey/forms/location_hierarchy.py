from django import forms
from django.forms.formsets import BaseFormSet
from survey.models.locations import *


class BaseArticleFormSet(BaseFormSet):

    def clean(self):
        for form_count in range(0, self.total_form_count()):
            form = self.forms[form_count]
            has_code = form.cleaned_data.get('has_code', None)
            code = form.cleaned_data.get('length_of_code', '')
            levels = form.cleaned_data.get('levels', '')

            if len(levels.strip()) == 0:
                message = "field cannot be empty."
                form._errors["levels"] = form.error_class([message])
                raise forms.ValidationError(message)

            if has_code:
                if not code:
                    message = "length of code cannot be blank if has code is checked."
                    form._errors["length_of_code"] = form.error_class([
                                                                      message])
                    raise forms.ValidationError(message)