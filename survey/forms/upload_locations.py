from django import forms


class UploadLocationForm(forms.Form):
    def __init__(self, data=None):
        super(UploadLocationForm, self).__init__(data=data)
        self.fields['file'] = forms.FileField(label='Location Input File', widget=forms.FileInput())