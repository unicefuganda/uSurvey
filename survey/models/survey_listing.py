__author__ = 'anthony <>'

from django.db import models
from survey.models.base import BaseModel
from survey.models.questions import Question, QuestionSet
from survey.models.interviews import Answer, MultiChoiceAnswer


class ListingTemplate(QuestionSet):

    class Meta:
        app_label = 'survey'

    @classmethod
    def verbose_name(cls):
        return 'Listing Form'


class ListingQuestion(Question):

    class Meta:
        app_label = 'survey'


class RandomizationCriterion(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    listing_template = models.ForeignKey(ListingTemplate, related_name='criteria')
    listing_question = models.ForeignKey(ListingQuestion, related_name='criteria')
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
        return CriterionTestArgument.objects.filter(group_condition=self).order_by('position')


class CriterionTestArgument(BaseModel):
    group_condition = models.ForeignKey(RandomizationCriterion)
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'
