from django import forms
from django.forms import ModelForm, ValidationError
import re
from django.conf import settings
from survey.models import QuestionTemplate, TemplateOption, Answer, QuestionModule, \
            HouseholdMemberGroup, MultiChoiceAnswer, MultiSelectAnswer, QuestionFlow


class QuestionTemplateForm(ModelForm):

    options = forms.CharField(max_length=50, widget=forms.HiddenInput(), required=False)
    
    def __init__(self, *args, **kwargs):
        super(QuestionTemplateForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['module', 'text', 'identifier', 'group', 'answer_type']
    
    class Meta:
        model = QuestionTemplate
        widgets ={
            'text': forms.Textarea(attrs={"rows":4, "cols":100,"maxlength":"150"}),
        }
        
    def clean_identifier(self):
        answer_type = self.cleaned_data.get('identifier', None)
        qts = QuestionTemplate.objects.filter(identifier=answer_type)
        if qts.exists():
            if not self.instance or not (self.instance.identifier == answer_type):
                raise ValidationError('Identifier already in use the question library')
        return self.cleaned_data['identifier']
        
    def clean_options(self):
        options = dict(self.data).get('options')
        if options:
            options = filter(lambda text: text.strip(), options)
            options = map(lambda option: re.sub("[%s]" % settings.USSD_IGNORED_CHARACTERS, '', option), options)
            options = map(lambda option: re.sub("  ", ' ', option), options)
            self.cleaned_data['options'] = options
        return options

    def clean(self):
        self.clean_options()
        answer_type = self.cleaned_data.get('answer_type', None)
        options = self.cleaned_data.get('options', None)
        text = self.cleaned_data.get('text', None)
        self._check__multichoice_and_options_compatibility(answer_type, options)
        self._strip_special_characters_for_ussd(text)
#         import pdb; pdb.set_trace()
        return self.cleaned_data

    def _check__multichoice_and_options_compatibility(self, answer_type, options):
        if answer_type in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()] and not options:
            message = 'Question Options missing.'
            self._errors['answer_type'] = self.error_class([message])
            del self.cleaned_data['answer_type']

        if answer_type not in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()] and options:
            del self.cleaned_data['options']

    def _strip_special_characters_for_ussd(self, text):
        if text:
            text = re.sub("[%s]" % settings.USSD_IGNORED_CHARACTERS, '', text)
            self.cleaned_data['text'] = re.sub("  ", ' ', text)

    def options_supplied(self, commit):
        return commit and self.cleaned_data.get('options', None)

    def save_question_options(self, question):
        order = 0
        options = self.cleaned_data['options']
        question.options.all().delete()
        for text in options:
            order += 1
            TemplateOption.objects.create(question=question, text=text, order=order)

    def save(self, commit=True, *args, **kwargs):
        question = super(QuestionTemplateForm, self).save(commit=commit, *args, **kwargs)
        if self.options_supplied(commit):
            self.save_question_options(question)
        return question