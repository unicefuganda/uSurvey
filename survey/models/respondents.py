__author__ = 'anthony <>'

from django.db import models
from model_utils.managers import InheritanceManager
from survey.models.base import BaseModel
from survey.models.questions import Question, QuestionSet
from survey.models.interviews import Answer, MultiChoiceAnswer, MultiSelectAnswer


class MetricsForm(QuestionSet):

    class Meta:
        app_label = 'survey'


class SurveyMetric(Question):
    metric_form = models.ForeignKey(MetricsForm, related_name='metric_form_questions')

    class Meta:
        app_label = 'survey'


class RespondentGroup(BaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField()
    metric_form = models.ForeignKey(MetricsForm, related_name='respondent_group')


class RespondentGroupCondition(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    respondent_group = models.ForeignKey(RespondentGroup, related_name='conditions')
    personal_info = models.ForeignKey(SurveyMetric, related_name='conditions')
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
    group_condition = models.ForeignKey(RespondentGroupCondition)
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'


