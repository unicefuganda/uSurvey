from survey.models.base import BaseModel
from django.db import models
from survey.models.question_module import QuestionModule
from survey.models.interviews import MultiChoiceAnswer, Answer
from survey.models.surveys import Survey
from survey.models.questions import Question


class Indicator(BaseModel):
    MEASURE_CHOICES = (('%', 'Percentage'),
                       ('Number', 'Count'))
    module = models.ForeignKey(QuestionModule, null=False, related_name='indicator')
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(null=True)
    measure = models.CharField(max_length=255, null=False, choices=MEASURE_CHOICES, default=MEASURE_CHOICES[0][1])
    batch = models.ForeignKey("Batch", null=True, related_name='indicators')

    def is_percentage_indicator(self):
        percentage_measure = [Indicator.MEASURE_CHOICES[
            0][1], Indicator.MEASURE_CHOICES[0][0]]
        return self.measure in percentage_measure

    def get_matching_interviews(self, batch, loc):
        pass

#
#
# class IndicatorCriterion(BaseModel):
#     VALIDATION_TESTS = [(validator.__name__, validator.__name__) for validator in Answer.validators()]
#     survey = models.ForeignKey(Survey, related_name='indicator_criteria')
#     test_question = models.ForeignKey(Question, related_name='criteria')
#     indicator_test = models.CharField(max_length=200, choices=VALIDATION_TESTS)
#
#     class Meta:
#         app_label = 'survey'
#
#     @property
#     def test_params(self):
#         return [t.param for t in self.text_arguments]
#
#     def params_display(self):
#         params = []
#         for arg in self.text_arguments:
#             if self.question.answer_type == MultiChoiceAnswer.choice_name():
#                 params.append(self.question.options.get(order=arg.param).text)
#             else:
#                 params.append(arg.param)
#
#         return params
#
#     def passes_test(self, value):
#         answer_class = Answer.get_class(self.listing_question.answer_type)
#         method = getattr(answer_class, self.validation_test, None)
#         if method is None:
#             raise ValueError('unsupported validator defined on listing question')
#         return method(value, *list(self.test_arguments))
#
#     def qs_passes_test(self, value_key, queryset):
#         answer_class = Answer.get_class(self.listing_question.answer_type)
#         method = getattr(answer_class, 'fetch_%s' % self.validation_test, None)
#         return method(value_key, *list(self.test_arguments), qs=queryset)
#
#     @property
#     def test_arguments(self):
#         return IndicatorTestArgument.objects.filter(test_condition=self).values_list('param',
#                                                                                      flat=True).order_by('position')
#
#
# class IndicatorTestArgument(BaseModel):
#     test_condition = models.ForeignKey(IndicatorCriterion, related_name='arguments')
#     position = models.PositiveIntegerField()
#     param = models.CharField(max_length=100)
#
#     def __unicode__(self):
#         return self.param
#
#     class Meta:
#         app_label = 'survey'
#         get_latest_by = 'position'
#
