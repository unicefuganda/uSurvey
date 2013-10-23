from django import forms

class UploadLocationForm(forms.Form):
    file = forms.FileField(label='Location Input File', required=True)

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.csv'):
            message = "The file extension should be .csv."
            self._errors['file'] = self.error_class([message])
            del self.cleaned_data['file']
        return file