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
	image = forms.FileField(
        label='Select a file',
        help_text='max. 42 megabytes'
    )
	class Meta:
		model = SuccessStories
		widgets = {
			'content': forms.Textarea(attrs={"rows": 10, 'cols': 40, "id": "content-editor"})
		}
		exclude = []
