from django import forms
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import LocationType
from survey.models import Survey, LocationTypeDetails
from survey.services.csv_uploader import CSVUploader, UploadService
from survey.services.location_upload import UploadLocation
from survey.services.location_weights_upload import UploadLocationWeights


class UploadCSVFileForm(forms.Form):
    file = forms.FileField(label='Location Input File', required=True)

    def __init__(self, uploader, *args, **kwargs):
        super(UploadCSVFileForm, self).__init__(*args, **kwargs)
        self.uploader = uploader

    def clean_file(self):
        _file = self.cleaned_data['file']
        if self._is_not_csv(_file):
            message = '%s is not a valid csv file.'%_file.name
            self._errors['file'] = self.error_class([message])
            del self.cleaned_data['file']
        return _file

    def _is_not_csv(self, _file):
        return '\0' in _file.read()

    def upload(self):
        _file = self.cleaned_data['file']
        uploader = self.uploader(_file)
        return uploader.upload()


class UploadLocationsForm(UploadCSVFileForm):
    def __init__(self,  *args, **kwargs):
        super(UploadLocationsForm, self).__init__(UploadLocation, *args, **kwargs)

    def clean(self, *args, **kwargs):
        super(UploadLocationsForm, self).clean(*args, **kwargs)
        if self.cleaned_data.get('file', None):
            self.clean_headers()
        return self.cleaned_data

    def clean_headers(self):
        _file = self.cleaned_data['file']
        headers = CSVUploader(_file).headers()
        for index, header in enumerate(headers):
            header = header.strip()
            if not header.endswith('Code'):
                header = header.replace('Name', '')
                location_type= self.clean_location_type(header)
                location_detail = self.clean_location_detail(location_type, header)
                self.clean_has_code(location_type, location_detail, headers, index)
        self.clean_headers_location_type_order(headers)
        return self.cleaned_data

    def clean_location_type(self, header):
        location_type = LocationType.objects.filter(name=header, slug=slugify(header))
        if not location_type.exists():
            raise ValidationError('Location type - %s not found.' % header)
        return location_type[0]

    def clean_location_detail(self, location_type, header):
        detail = location_type.details.all()
        if not detail:
            raise ValidationError('Location type details for %s not found.'% header)
        return detail[0]

    def clean_has_code(self, type, location_detail, headers, index):
        if location_detail.has_code:
            if index == 0 or headers[index-1].replace('Code', '') != type.name:
                raise ValidationError('%sCode column should be before %sName column. Please refer to input file format.'%(type.name, type.name))
        else:
            if headers[index-1].replace('Code', '') == type.name:
                raise ValidationError('%s has no code. The column %sCode should be removed. Please refer to input file format.'%(type.name, type.name))

    def clean_headers_location_type_order(self, headers):
        headers = UploadService.remove_trailing('Name', in_array=headers, exclude='Code')
        ordered_types = [type.name for type in LocationTypeDetails.get_ordered_types().exclude(name__iexact='country')]
        if not ordered_types == headers:
            raise ValidationError('Location types not in order. Please refer to input file format.')


class UploadWeightsForm(UploadCSVFileForm):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), empty_label=None)

    def __init__(self,  *args, **kwargs):
        super(UploadWeightsForm, self).__init__(UploadLocationWeights, *args, **kwargs)
        self.fields.keyOrder = ['survey', 'file']
        self.fields['file'].label = 'Location weights file'

    def upload(self):
        _file = self.cleaned_data['file']
        survey = self.cleaned_data['survey']
        uploader = self.uploader(_file)
        return uploader.upload(survey)
