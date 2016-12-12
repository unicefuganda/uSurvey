__author__ = 'anthony <>'

from django.db import models
from model_utils.managers import InheritanceManager
from survey.models.base import BaseModel
from survey.models.generics import TemplateQuestion
from survey.models.questions import Question, QuestionSet
from survey.models.interviews import Answer, MultiChoiceAnswer, MultiSelectAnswer


class ParameterTemplate(TemplateQuestion):

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return self.identifier


class RespondentGroup(BaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def has_interviews(self):
        from survey.models import Interview
        return self.questions.exists() and Interview.objects.filter(qset__pk=self.questions.first().qset.pk).exists()


class RespondentGroupCondition(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    respondent_group = models.ForeignKey(RespondentGroup, related_name='group_conditions')
    test_question = models.ForeignKey(ParameterTemplate, related_name='group_condition')
    validation_test = models.CharField(
        max_length=200, null=True, blank=True, choices=VALIDATION_TESTS)

    class Meta:
        app_label = 'survey'

    @property
    def test_params(self):
        return [t.param for t in self.text_arguments]

    def params_display(self):
        params = []
        for arg in self.text_arguments:
            if self.question.answer_type == MultiChoiceAnswer.choice_name():
                params.append(self.question.options.get(order=arg.param).text)
            else:
                params.append(arg.param)

        return params

    @property
    def test_arguments(self):
        return GroupTestArgument.objects.filter(group_condition=self).order_by('position')


class GroupTestArgument(BaseModel):
    group_condition = models.ForeignKey(RespondentGroupCondition, related_name='arguments')
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'


class SurveyParameterList(QuestionSet): # basically used to tag survey grouping questions

    class Meta:
        app_label = 'survey'