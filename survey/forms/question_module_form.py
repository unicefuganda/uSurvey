from django.core.exceptions import ValidationError
from django.forms import ModelForm, forms
from survey.models import QuestionModule


class QuestionModuleForm(ModelForm):

    def clean_name(self):
        name = self.cleaned_data['name']
        creating_new_module = not self.instance.id
        editing_module = self.instance.name and self.instance.name != name
        if (creating_new_module or editing_module) and QuestionModule.objects.filter(name=name):
            raise ValidationError("Module with name %s already exists." % name)
        return self.cleaned_data['name']

    class Meta:
        model = QuestionModule
        exclude = []
        widgets = {
            'description': forms.Textarea(attrs={"rows": 3, "cols": 30})
        }
