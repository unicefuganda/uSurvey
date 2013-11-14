from django import forms
from survey.models import Survey
from survey.services.location_upload import UploadLocation
from survey.services.location_weights_upload import UploadLocationWeights


class UploadCSVFileForm(forms.Form):
    file = forms.FileField(label='Location Input File', required=True)

    def __init__(self, uploader, *args, **kwargs):
        super(UploadCSVFileForm, self).__init__(*args, **kwargs)
        self.uploader = uploader

    def clean_file(self):
        _file = self.cleaned_data['file']
        if not _file.name.endswith('.csv'):
            message = "The file extension should be .csv."
            self._errors['file'] = self.error_class([message])
            del self.cleaned_data['file']
        return _file

    def upload(self):
        _file = self.cleaned_data['file']
        uploader = self.uploader(_file)
        return uploader.upload()


class UploadLocationsForm(UploadCSVFileForm):
    def __init__(self,  *args, **kwargs):
        super(UploadLocationsForm, self).__init__(UploadLocation, *args, **kwargs)


class UploadWeightsForm(UploadCSVFileForm):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), empty_label=None)

    def __init__(self,  *args, **kwargs):
        super(UploadWeightsForm, self).__init__(UploadLocationWeights, *args, **kwargs)

    def upload(self):
        _file = self.cleaned_data['file']
        survey = self.cleaned_data['survey']
        uploader = self.uploader(_file)
        return uploader.upload(survey)
