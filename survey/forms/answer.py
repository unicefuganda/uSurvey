__author__ = 'anthony'
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django import forms
from form_helper import FormOrderMixin, get_form_field_no_validation
from survey.models import (
    ListingSample,
    Answer,
    Interview,
    VideoAnswer,
    AudioAnswer,
    ImageAnswer,
    TextAnswer,
    NumericalAnswer,
    MultiChoiceAnswer,
    MultiSelectAnswer,
    DateAnswer,
    SurveyAllocation,
    EnumerationArea,
    Survey,
    QuestionSet,
    Interviewer,
    InterviewerAccess,
    USSDAccess,
    QuestionOption,
    GeopointAnswer)


class USSDSerializable(object):

    def render_prepend_ussd(self):
        if 'value' in self.fields:
            return self.fields['value'].label
        return ''

    def render_extra_ussd(self):
        """Basically used by implementing classes\
        to render ussd versions of their forms
        :return:
        """
        pass

    def render_extra_ussd_html(self):
        """Basically used by implementing classes to render
        \ussd Preview versions of their forms on HTML
        :return:
        """
        pass

    def text_error(self):
        if self.errors:
            return self.errors['value'][0]


def get_answer_form(interview, access=None):
    question = interview.last_question
    answer_class = Answer.get_class(question.answer_type)
    if access is None:
        access = InterviewerAccess.get(id=interview.interview_channel.id)
    else:
        access = access

    class AnswerForm(forms.ModelForm, USSDSerializable):

        class Meta:
            model = answer_class
            fields = ['value']

        def __init__(self, *args, **kwargs):
            super(AnswerForm, self).__init__(*args, **kwargs)
            #>self.fields['uid'] = forms.CharField(initial=access.user_identifier, widget=forms.HiddenInput)
            if question.answer_type == DateAnswer.choice_name():
                self.fields['value'] = forms.DateField(
                    label='Answer',
                    input_formats=[
                        settings.DATE_FORMAT,
                    ],
                    widget=forms.DateInput(
                        attrs={
                            'placeholder': 'Date Of Birth',
                            'class': 'datepicker'},
                        format=settings.DATE_FORMAT))
            if question.answer_type == GeopointAnswer.choice_name():
                model_field = get_form_field_no_validation(forms.CharField)
                self.fields['value'] = model_field(label='Answer', widget=forms.TextInput(
                    attrs={'placeholder': 'Lat[space4]Long[space4' 'Altitude[space4]Precision'}))
            if question.answer_type == MultiChoiceAnswer.choice_name():
                self.fields['value'] = forms.ChoiceField(choices=[(opt.order, opt.text) for opt
                                                                  in question.options.all()], widget=forms.RadioSelect)
                self.fields['value'].empty_label = None
            if access.choice_name() == USSDAccess.choice_name():
                self.fields['value'].widget = forms.NumberInput()
            if question.answer_type == MultiSelectAnswer.choice_name():
                self.fields['value'] = forms.ModelMultipleChoiceField(
                    queryset=question.options.all(), widget=forms.CheckboxSelectMultiple)
            accept_types = {AudioAnswer.choice_name(): 'audio/*',
                            VideoAnswer.choice_name(): 'video/*',
                            ImageAnswer.choice_name(): 'image/*'
                            }
            if question.answer_type in [
                    AudioAnswer.choice_name(),
                    VideoAnswer.choice_name(),
                    ImageAnswer.choice_name()]:
                self.fields['value'].widget.attrs = {
                    'accept': accept_types.get(
                        question.answer_type, '|'.join(
                            accept_types.values()))}
            if access.choice_name() == USSDAccess.choice_name():
                self.fields['value'].label = ''
            else:
                self.fields['value'].label = 'Answer'

        def full_clean(self):
            try:
                return super(AnswerForm, self).full_clean()
            except ValueError:
                if question.answer_type == GeopointAnswer.choice_name():
                    self.cleaned_data['value'] = self.data['value']
                else:
                    raise

        def render_extra_ussd(self):
            text = []
            if question.options.count() > 0:
                map(lambda opt: text.append('%s: %s' %
                                            (opt.order, opt.text)), question.options.all())
            elif hasattr(interview.last_question, 'loop_started'):
                text.append('%s: %s' %
                            (question.text, self.initial.get('value', 1)))
                text.append('Enter any key to continue')
            return mark_safe('\n'.join(text))

        def render_extra_ussd_html(self):
            text = []
            if question.options.count() > 0:
                map(lambda opt: text.append('%s: %s' %
                                            (opt.order, opt.text)), question.options.all())
            elif hasattr(interview.last_question, 'loop_started'):
                text.append('%s: %s' %
                            (question.text, self.initial.get('value', 1)))
            return mark_safe('<br />'.join(text))

        def clean_value(self):
            if question.answer_type == MultiChoiceAnswer.choice_name():
                try:
                    self.cleaned_data['value'] = question.options.get(
                        order=self.cleaned_data['value'])
                except QuestionOption.DoesNotExist:
                    raise ValidationError('Please select a valid option')
            if question.answer_type == GeopointAnswer.choice_name():
                float_entries = self.cleaned_data['value'].split(' ')
                valid = False
                try:
                    map(lambda entry: float(entry), float_entries)
                    if len(float_entries) == 4:
                        valid = True
                except BaseException:
                    pass
                if not valid:
                    raise ValidationError(
                        'Please enter in format: lat[space]long[space]altitude[space]precision')
            return self.cleaned_data['value']

        def save(self, *args, **kwargs):
            return answer_class.create(
                interview, question, self.cleaned_data['value'])

    return AnswerForm


class BaseSelectInterview(forms.ModelForm):

    def __init__(self, request, access, *args, **kwargs):
        super(BaseSelectInterview, self).__init__(*args, **kwargs)
        self.access = access
        if 'data' in kwargs:
            kwargs['data']._mutable = True
            kwargs['data']['uid'] = access.user_identifier
            kwargs['data']._mutable = False
        if request.user.is_authenticated():
            self.user = request.user
        else:
            self.user = None
        self.interviewer = access.interviewer
        self.fields['uid'] = forms.CharField(
            initial=access.user_identifier,
            widget=forms.HiddenInput)

    class Meta:
        model = Interview
        fields = []

    def save(self, commit=True):
        if self.user:
            instance = super(BaseSelectInterview, self).save(commit=False)
            instance.uploaded_by = self.user
            if commit:
                instance.save()
            return instance
        else:
            return super(BaseSelectInterview, self).save(commit=commit)


class AddMoreLoopForm(BaseSelectInterview, USSDSerializable):
    """Just looks like answer form. But used to confirm whether to continue loop for user selected loop scenarios
    """
    ADD_MORE = 1
    DO_NOT_ADD = 2
    CHOICES = [(ADD_MORE, 'Yes'), (DO_NOT_ADD, 'No')]

    def __init__(self, request, access, *args, **kwargs):
        super(AddMoreLoopForm, self).__init__(request, access, *args, **kwargs)
        self.fields['value'] = forms.ChoiceField(choices=self.CHOICES, widget=forms.RadioSelect)
        if self.access.choice_name() == USSDAccess.choice_name():
            self.fields['value'].widget = forms.NumberInput()
        if access.choice_name() == USSDAccess.choice_name():
            self.fields['value'].label = ''
        else:
            self.fields['value'].label = 'Answer'

    def render_extra_ussd(self):
        text = []
        map(lambda choice: text.append('%s: %s' % choice), self.CHOICES)
        return mark_safe('\n'.join(text))

    def render_extra_ussd_html(self):
        text = []
        map(lambda choice: text.append('%s: %s' % choice), self.CHOICES)
        return mark_safe('<br />'.join(text))

    class Meta:
        model = Interview
        fields = []


class UserAccessForm(forms.Form):
    uid = forms.CharField(label='Mobile/ODK ID', max_length=25)

    def text_error(self):
        if self.errors:
            return self.errors['uid'][0]

    def clean_uid(self):
        try:
            access = InterviewerAccess.get(
                user_identifier=self.cleaned_data['uid'])
        except InterviewerAccess.DoesNotExist:
            raise ValidationError('No such interviewer')
        return access


class UssdTimeoutForm(forms.Form):
    use_timeout = forms.ChoiceField(
        widget=forms.RadioSelect, choices=[
            (1, 'Use Timeout'), (2, 'No Timeout')], initial=2, label='')


class SurveyAllocationForm(
        BaseSelectInterview,
        FormOrderMixin,
        USSDSerializable):

    def __init__(self, request, access, *args, **kwargs):
        super(SurveyAllocationForm, self).__init__(request, access, *args, **kwargs)
        self.CHOICES = [(idx + 1, sa.allocation_ea.name) for idx, sa
                        in enumerate(self.interviewer.unfinished_assignments.order_by('allocation_ea__name'))]
        self.fields['value'] = forms.ChoiceField(choices=self.CHOICES,widget=forms.RadioSelect)
        if self.access.choice_name() == USSDAccess.choice_name():
            self.fields['value'].widget = forms.NumberInput()
        self.fields['value'].label = 'Select EA'
        self.order_fields(['value', 'test_data'])

    def render_extra_ussd(self):
        text = []
        map(lambda choice: text.append('%s: %s' % choice), self.CHOICES)
        return mark_safe('\n'.join(text))

    def render_extra_ussd_html(self):
        text = []
        map(lambda choice: text.append('%s: %s' % choice), self.CHOICES)
        return mark_safe('<br />'.join(text))

    def clean_value(self):
        selected = int(self.cleaned_data['value'])
        return self.interviewer.unfinished_assignments.order_by(
            'allocation_ea__name')[selected - 1].allocation_ea

    def selected_allocation(self):
        if self.is_valid():
            selected = int(self.data['value'])
            return self.interviewer.unfinished_assignments.order_by('allocation_ea__name')[
                selected - 1]

    def save(self, commit=True):
        instance = super(SurveyAllocationForm, self).save(commit=commit)
        instance.survey = self.selected_allocation().survey
        instance.ea = self.cleaned_data['value']
        instance.interviewer = self.interviewer
        return instance

    class Meta:
        model = Interview
        fields = ['test_data', ]


class ReferenceInterviewForm(BaseSelectInterview, USSDSerializable):
    """Basically used to select random sample for sampled surveys
    """

    def __init__(self, request, access, survey, allocation_ea, *args, **kwargs):
        super(ReferenceInterviewForm, self).__init__(request, access, *args, **kwargs)
        self.survey = survey
        self.random_samples = ListingSample.get_or_create_samples(survey, allocation_ea).order_by('interview__created')
        choices = [(idx + 1, sample.get_display_label()) for idx, sample in enumerate(self.random_samples)]
        self.fields['value'] = forms.ChoiceField(choices=choices, widget=forms.RadioSelect)
        if self.access.choice_name() == USSDAccess.choice_name():
            self.fields['value'].widget = forms.NumberInput()
        self.listing_form = survey.preferred_listing.listing_form if survey.preferred_listing else survey.listing_form
        self.fields['value'].label = 'Select %s' % self.listing_form.name

    def clean_value(self):
        selected = int(self.cleaned_data['value'])
        return self.random_samples.values_list('interview', flat=True)[selected - 1]

    def render_extra_ussd(self):
        text = []
        map(lambda choice: text.append('%s: %s' %
                                       choice), self.fields['value'].choices)
        return mark_safe('\n'.join(text))

    def render_extra_ussd_html(self):
        text = []
        map(lambda choice: text.append('%s: %s' %
                                       choice), self.fields['value'].choices)
        return mark_safe('<br />'.join(text))


class SelectBatchForm(BaseSelectInterview, USSDSerializable):

    def __init__(self, request, access, survey, *args, **kwargs):
        super(SelectBatchForm, self).__init__(request, access, *args, **kwargs)
        self.survey = survey
        self.batches = survey.batches.all().order_by('name')
        self.fields['value'] = forms.ChoiceField()
        self.fields['value'].choices = [(idx + 1, batch.name) for idx, batch in enumerate(self.batches)]
        self.fields['value'].label = 'Select Batch'

    def clean_value(self):
        selected = int(self.cleaned_data['value'])
        return self.batches[selected - 1]

    def render_extra_ussd(self):
        text = []
        map(lambda choice: text.append('%s: %s' %
                                       choice), self.fields['value'].choices)
        return mark_safe('\n'.join(text))

    def render_extra_ussd_html(self):
        text = []
        map(lambda choice: text.append('%s: %s' %
                                       choice), self.fields['value'].choices)
        return mark_safe('<br />'.join(text))


class SelectInterviewerForm(forms.Form):
    interviewer = forms.ModelChoiceField(queryset=Interviewer.objects.all())

    class Meta:
        widgets = {
            'interviewer': forms.Select(attrs={'class': 'chzn-select', }),
        }
