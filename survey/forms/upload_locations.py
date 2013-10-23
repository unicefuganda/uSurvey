from django import forms
from survey.views.location_upload_view_helper import UploadLocation


class UploadLocationForm(forms.Form):
    file = forms.FileField(label='Location Input File', required=True)

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.csv'):
            message = "The file extension should be .csv."
            self._errors['file'] = self.error_class([message])
            del self.cleaned_data['file']
        return file

    def upload(self):
        file = self.cleaned_data['file']
        uploader = UploadLocation(file)
        return uploader.upload()