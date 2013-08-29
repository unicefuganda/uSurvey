from django import forms
from survey.models import *
from django.forms import ModelForm
from django.core.validators import *

class QuestionForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['answer_type'].choices = list(Question.TYPE_OF_ANSWERS)

    class Meta:
        model = Question
        fields =['text','answer_type']
