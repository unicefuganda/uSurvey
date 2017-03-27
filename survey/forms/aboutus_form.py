from django.forms import ModelForm, forms
from survey.models import AboutUs, SuccessStories


class AboutUsForm(ModelForm):

    class Meta:
        model = AboutUs
        widgets = {
            'content': forms.Textarea(attrs={"rows": 10, 'cols': 40, "id": "content-editor"})
        }
        exclude = []

class SuccessStoriesForm(ModelForm):
	print "hello"

	class Meta:
		model = SuccessStories
		widgets = {
			'content': forms.Textarea(attrs={"rows": 10, 'cols': 40, "id": "content-editor"})
		}
		exclude = []
