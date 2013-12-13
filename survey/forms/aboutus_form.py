from django.forms import ModelForm, forms
from survey.models import AboutUs


class AboutUsForm(ModelForm):
    class Meta:
        model = AboutUs
        widgets = {
                    'content': forms.Textarea(attrs={"rows": 10, 'cols': 40, "id": "content-editor"})
        }
