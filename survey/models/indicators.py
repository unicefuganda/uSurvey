from survey.models.base import BaseModel
from django.db import models
from survey.models.question_module import QuestionModule
from survey.models.interviews import MultiChoiceAnswer, Answer
from survey.models.surveys import Survey
from survey.models import Batch
from survey.models import BatchQuestion
from survey.models import Question


class Indicator(BaseModel):
    PERCENTAGE = 1
    COUNT = 2
    name = models.CharField(max_length=255, null=False)
    # module = models.ForeignKey(QuestionModule, null=False, related_name='indicator')
    description = models.TextField(null=True)
    parameter = models.ForeignKey(BatchQuestion, related_name='indicators')

    def is_percentage_indicator(self):
        percentage_measure = [Indicator.MEASURE_CHOICES[
            0][1], Indicator.MEASURE_CHOICES[0][0]]
        return self.measure in percentage_measure

    def get_matching_interviews(self, batch, loc):
        pass

    def compute_for_next_location_type_in_the_hierarchy(self, current_location):
        locations = current_location.get_children()
        data = {}
        for location in locations:
            data[location] = self.compute_for_location(location)
        return data

    # def compute_for_location(self, location):
    #     interviewers = Interviewer.lives_under_location(location)
    #     if self.numerator.is_multichoice():
    #         return self.compute_multichoice_question_for_interviewers(interviewers)
    #     else:
    #         return self.compute_numerical_question_for_interviewers(interviewers)


class IndicatorCriteria(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    indicator = models.ForeignKey(Indicator, related_name='indicator_criteria')
    # batch & parameter_list questions
    test_question = models.ForeignKey(Question, related_name='indicator_criteria', verbose_name='parameter')
    validation_test = models.CharField(max_length=200, choices=VALIDATION_TESTS, verbose_name='operator')

    class Meta:
        app_label = 'survey'

    @property
    def test_params(self):
        return [t.param for t in self.test_arguments]

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
        return IndicatorCriteriaTestArgument.objects.filter(criteria=self).order_by('position')

    def qs_passes_test(self, value_key, queryset):
        answer_class = Answer.get_class(self.test_question.answer_type)
        method = getattr(answer_class, 'fetch_%s' % self.validation_test, None)
        return method(value_key, *list(self.test_arguments), qs=queryset)


class IndicatorCriteriaTestArgument(BaseModel):
    criteria = models.ForeignKey(IndicatorCriteria, related_name='arguments')
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'
