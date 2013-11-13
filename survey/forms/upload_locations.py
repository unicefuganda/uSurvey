from django import forms

class UploadCSVFileForm(forms.Form):
    file = forms.FileField(label='Location Input File', required=True)

    def __init__(self, uploader, *args, **kwargs):
        super (UploadCSVFileForm, self).__init__(*args, **kwargs)
        self.uploader = uploader

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.csv'):
            message = "The file extension should be .csv."
            self._errors['file'] = self.error_class([message])
            del self.cleaned_data['file']
        return file

    def upload(self):
        file = self.cleaned_data['file']
        uploader = self.uploader(file)
        return uploader.upload()