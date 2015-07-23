from django import forms
from django.forms import ModelForm
import re
from survey.models import Question, QuestionFlow, Batch, MultiSelectAnswer, MultiChoiceAnswer, QuestionModule
from survey.models.householdgroups import HouseholdMemberGroup


class QuestionForm(ModelForm):
    text = forms.CharField(label='Respond with ', max_length=150, 
                                    widget=forms.Textarea(attrs={"id" : "question", "rows":4, "cols":100,"maxlength":"150", "class": "batch_questions question_form"})
                                    )
    identifier = forms.CharField(label='Save reply as', max_length=100, widget=forms.TextInput(attrs={"id": 'identifier', "class": "batch_questions  question_form"}))
#     answer_type = forms.CharField(widget=forms.Select(attrs={"id": 'answer_type', "class": "batch_questions question_form"}))
    
    def __init__(self, batch, data=None, initial=None, instance=None):
        super(QuestionForm, self).__init__(data=data, initial=initial, instance=instance)
#         import pdb; pdb.set_trace();
        self.fields['answer_type'].choices = [(name, name) for name in batch.answer_types]
                
    class Meta:
        model = Question
        fields =[ 'text', 'identifier', 'answer_type', ]

        widgets ={
#             'text': forms.Textarea(attrs={"id" : "question", "rows":4, "cols":100,"maxlength":"150", "class": "batch_questions question_form"}),
#             'identifier': forms.TextInput(attrs={"id": 'identifier', "class": "batch_questions  question_form"}),
             'answer_type' : forms.Select(attrs={"id": 'answer_type', "class": "batch_questions question_form"}),
        }


    def save(self, commit=True, **kwargs):
        question = super(QuestionForm, self).save(commit=False)
        if commit:
            maximum_order = HouseholdMemberGroup.objects.get(id=kwargs['group'][0]).maximum_question_order()
            order = maximum_order + 1 if maximum_order else 1
            question.order = order
            question.save()

        if self.kwargs_has_batch(**kwargs):
            question.batches.add(kwargs['batch'])

        if self.options_supplied(commit):
            self.save_question_options(question)
        return question
    
class QuestionFlowForm(forms.Form):
    
    validation_test = forms.CharField(label='If response... ', max_length=200, 
                                      widget=forms.Select(choices=QuestionFlow.VALIDATION_TESTS, 
                                                          attrs={"id": 'validation_test', "class": "batch_questions question_flow_form"}))
    validation_arg = forms.CharField(label='', max_length=200, 
                                    widget=forms.TextInput(attrs={ "id": 'validation_arg', "class": "batch_questions question_flow_form validation_arg", }), 
                                    required=False)
#     text = forms.CharField(label='', max_length=150, 
#                                     widget=forms.Textarea(attrs={"id" : "question", "rows":4, "cols":100,"maxlength":"150", "class": "batch_questions question_form"}), 
#                                     )
#     identifier = forms.CharField(label='Save reply as', max_length=100, widget=forms.TextInput(attrs={"id": 'identifier', "class": "batch_questions  question_form"}))
#     answer_type = forms.CharField(widget=forms.Select(attrs={"id": 'answer_type', "class": "batch_questions question_form"}))
    
#     def __init__(self, batch, data=None, initial=None, instance=None):
#         super(QuestionFlowForm, self).__init__(data=data, initial=initial, instance=instance)
#         self.fields['answer_type'].choices = [(name, name) for name in batch.answer_types]
    
    class Meta:
        model = QuestionFlow
        exclude = ['question', 'next_question']
#         widgets = {
#             'question': forms.HiddenInput(),
#              "next_question" : forms.HiddenInput(),
#         }

    