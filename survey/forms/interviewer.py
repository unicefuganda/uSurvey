from django import forms
from django.forms import ModelForm
from survey.models import EnumerationArea
from survey.models import Interviewer
from survey.models import ODKAccess
from survey.models import Survey
from survey.models import SurveyAllocation
from survey.models import USSDAccess
from survey.models import LocationType
from django.conf import settings
from django.core.exceptions import ValidationError
import phonenumbers


class InterviewerForm(ModelForm):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), required=False)
    date_of_birth = forms.DateField(
        label="Date of birth",
        required=True,
        input_formats=[
            settings.DATE_FORMAT,
        ],
        widget=forms.DateInput(
            attrs={
                'placeholder': 'Date Of Birth',
                'class': 'datepicker'},
            format=settings.DATE_FORMAT))
    ea = forms.ModelMultipleChoiceField(
        queryset=EnumerationArea.objects.none(),
        help_text='Needs at least one %location to be selected',
        widget=forms.SelectMultiple(
            attrs={
                'class': 'chzn-select ea_filter ',
                'placeholder': 'Choose Multiple EAs',
                'data-placeholder': 'Search/Choose Multiple EAs',
            }), required=True)

    def __init__(self, eas, data=None, *args, **kwargs):
        """First parameter might be removed in the future since eas is just defined based on data value for performance
        :param eas:
        :param data:
        :param args:
        :param kwargs:
        :return:
        """
        super(InterviewerForm, self).__init__(data=data, *args, **kwargs)
        self.fields.keyOrder = [
            'name',
            'gender',
            'date_of_birth',
            'level_of_education',
            'language',
            'ea',
            'survey']
        self.fields['ea'].label = 'Enumeration Area'
        if self.instance:
            try:
                self.fields['survey'].initial = SurveyAllocation.objects.filter(
                    interviewer=self.instance,
                    status__in=[
                        SurveyAllocation.PENDING,
                        SurveyAllocation.COMPLETED]).order_by('status')[0].survey.pk
                self.fields['ea'].initial = EnumerationArea.objects.filter(id__in=[
                    assignment.allocation_ea.id for assignment in self.instance.unfinished_assignments
                ])
            except IndexError:
                pass
        self.fields['ea'].queryset = eas
        if self.data.get('ea'):
            self.fields['ea'].queryset = EnumerationArea.objects.filter(id__in=data.getlist('ea'))
        self.fields['survey'].empty_label = 'Select Survey'

    class Meta:
        model = Interviewer
        fields = ['name', 'date_of_birth', 'gender',
                  'level_of_education', 'language', ]
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'placeholder': 'Name'}), 'gender': forms.RadioSelect(
                choices=(
                    (True, 'Male'), (False, 'Female'))), }

    def clean_survey(self):
        eas = self.cleaned_data.get('ea', [])
        survey = self.cleaned_data['survey']
        if survey:
            # check if this has already been allocated to someone else
            allocs = SurveyAllocation.objects.filter(
                survey=survey,
                status__in=[
                    SurveyAllocation.PENDING,
                    SurveyAllocation.COMPLETED,
                ],
                interviewer__ea__in=eas,
                allocation_ea__in=eas).exclude(
                interviewer=self.instance)
            # if self.instance and self.instance.pk:
            #     allocs = allocs.exclude(interviewer=self.instance)
            if allocs.exists():
                raise ValidationError(
                    'Survey already active for %s interviewers. Starting from %s for \
                    Interviewer %s' % (allocs[0].allocation_ea, allocs[0].interviewer))
        return survey

    # def clean(self):
    #     ea_id = self.data.get('ea')
    #     #check if interviewer is already active with survey in current EA
    #     if self.instance and self.instance.pk and ea_id != self.instance.ea.pk and self.instance.has_survey():
    #         raise ValidationError('Interviewer is having an active survey')
    #     return self.cleaned_data

    def save(self, commit=True, **kwargs):
        interviewer = super(InterviewerForm, self).save(commit=commit, **kwargs)
        eas = self.cleaned_data['ea']
        interviewer.ea = eas[0]
        if commit:
            survey = self.cleaned_data['survey']
            if survey:
                interviewer.assignments.update(      # I want to track every change in allocation
                    status=SurveyAllocation.DEALLOCATED, survey=survey)
                for ea in eas:
                    SurveyAllocation.objects.create(survey=survey,
                                                    interviewer=interviewer,
                                                    allocation_ea=ea)
            interviewer.save()
        return interviewer


class USSDAccessForm(ModelForm):
    user_identifier = forms.CharField(
        label='Mobile Number',
        max_length=settings.MOBILE_NUM_MAX_LENGTH,
        min_length=settings.MOBILE_NUM_MIN_LENGTH,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Format: 771234567',
                'style': "width:172px; margin-top:5px;",
                'maxlength': settings.MOBILE_NUM_MAX_LENGTH,
                'minlength': settings.MOBILE_NUM_MIN_LENGTH}))

    def __init__(self, *args, **kwargs):
        super(USSDAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['is_active', 'user_identifier', ]

    class Meta:
        model = USSDAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer', 'aggregator']

    def clean_user_identifier(self):
        identifier = self.cleaned_data.get('user_identifier', '')
        try:
            identifier = phonenumbers.parse(identifier, settings.COUNTRY_CODE)
            if phonenumbers.is_valid_number_for_region(
                    identifier, settings.COUNTRY_CODE):
                self.cleaned_data[
                    'user_identifier'] = identifier.national_number
            else:
                raise ValidationError('Invalid mobile number for your region')
        except phonenumbers.NumberParseException:
            raise ValidationError('Invalid mobile number')
        accesses = USSDAccess.objects.filter(
            user_identifier=identifier.national_number)
        if self.instance and accesses.exclude(
                interviewer=self.instance.interviewer).exists():
            raise ValidationError(
                'This mobile number is already in use by %s' %
                accesses. exclude(
                    interviewer=self.instance.interviewer)[0].interviewer.name)
        return self.cleaned_data['user_identifier']


class ODKAccessForm(ModelForm):
    user_identifier = forms.CharField(label='ODK ID')

    def __init__(self, *args, **kwargs):
        super(ODKAccessForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['is_active', 'user_identifier', 'odk_token', ]
        self.fields['odk_token'].label = 'ODK TOKEN'

    def clean_user_identifier(self):
        identifier = self.cleaned_data.get('user_identifier', '')
        accesses = ODKAccess.objects.filter(user_identifier=identifier)
        if self.instance:
            try:
                accesses = accesses.exclude(
                    interviewer=self.instance.interviewer)
            except Interviewer.DoesNotExist:
                pass
        if accesses.exists():
            raise ValidationError(
                'This ODK ID is already in use by %s' %
                accesses[0].interviewer.name)
        return self.cleaned_data['user_identifier']

    class Meta:
        model = ODKAccess
        exclude = ['reponse_timeout', 'duration', 'interviewer']
