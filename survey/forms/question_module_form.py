from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models import QuestionModule


class QuestionModuleForm(ModelForm):

    def clean_name(self):
        name = self.cleaned_data['name']
        if QuestionModule.objects.filter(name=name):
            raise  ValidationError("Module with name %s already exists." % name)
        return self.cleaned_data['name']

    class Meta:
        model = QuestionModule
