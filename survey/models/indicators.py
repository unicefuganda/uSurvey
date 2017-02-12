from survey.models.base import BaseModel
from django.db import models
from django.utils.datastructures import SortedDict
from survey.models.question_module import QuestionModule
from survey.models.interviews import MultiChoiceAnswer, Answer
from survey.models.surveys import Survey
from survey.models import Batch
from survey.models import BatchQuestion
from survey.models import Question, Interview



class Indicator(BaseModel):
    PERCENTAGE = 1
    COUNT = 2
    name = models.CharField(max_length=255, null=False)
    # module = models.ForeignKey(QuestionModule, null=False, related_name='indicator')
    description = models.TextField(null=True)
    batch = models.ForeignKey(Batch, related_name='indicators')
    formulae = models.TextField()        # I'm allowing that the formula can contain long names
    # parameter = models.ForeignKey(BatchQuestion, related_name='indicators', null=True, blank=True)

    def __unicode__(self):
        return self.name

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

    def get_data(self, locations, metric, presenter, *args, **kxargs):
        """Basically would be used to get presentation data for the indicators.
        presenter is a function to be called as:
        presenter(tabulated_data, child_location, loc_answers, options, factor, *args, **kwargs)
        where tabulated_data is the data dict to be incrementally populated by presenter for a single child loc
        loc_answers is just a filter set of answers for the particular child loc (after applying all criteria)
        child_location is one loc under locations, factor is the multiple to the count of filtered answers
        options is a queryset of QuestionOptions
        *args and kwargs are essentially parameters passed on directly to the function
        :param locations:
        :param metric:
        :param presenter: This is essentially a function to be called
        :param args:
        :param kwargs:
        :return:
        """
        tabulated_data = SortedDict()
        location_names = []
        options = self.parameter.options.order_by('order')
        answer_class = Answer.get_class(self.parameter.answer_type)
        kwargs = {}
        if self.indicator_criteria.count():
            kwargs['interview__in'] = self.applicable_interviews(locations)
        for child_location in locations:
            location_names.append(child_location.name)
            kwargs.update({
                'question__id': self.parameter.id,
                'interview__ea__locations__in': child_location.get_leafnodes(include_self=True)
            })
            loc_answers = answer_class.objects.filter(**kwargs)
            loc_total = loc_answers.count()
            factor = 1
            if loc_total > 0 and metric == Indicator.PERCENTAGE:
                factor = float(100)/ loc_total
            presenter(tabulated_data, child_location, loc_answers, options, factor, *args, **kxargs)
            #tabulated_data[child_location.name] = loc_answers.filter(value__pk=option_id).count()*factor
        return tabulated_data

    def applicable_interviews(self, locations):
        # the listed interviews in the ea
        valid_interviews = Interview.objects.filter(ea__locations__in=locations,
                                                    question_set__pk=self.parameter.qset.id,
                                                    survey=self.parameter.e_qset.survey,
                                                    ).values_list('id', flat=True)
        # now get the interviews that meet the randomization criteria
        for criterion in self.indicator_criteria.all():  # need to optimize this
            answer_type = criterion.test_question.answer_type
            if answer_type == MultiChoiceAnswer.choice_name():
                value_key = 'value__text'
            else:
                value_key = 'value'
            answer_class = Answer.get_class(answer_type)
            kwargs = {
                'question': criterion.test_question,
                'interview__id__in': valid_interviews
            }
            valid_interviews = criterion.qs_passes_test(value_key, answer_class.objects.filter(**kwargs).
                                                        only('interview__id').values_list('interview__id', flat=True))
        # return all the interviews that meet the criteria
        return valid_interviews
    # def compute_for_location(self, location):
    #     interviewers = Interviewer.lives_under_location(location)
    #     if self.numerator.is_multichoice():
    #         return self.compute_multichoice_question_for_interviewers(interviewers)
    #     else:
    #         return self.compute_numerical_question_for_interviewers(interviewers)


class IndicatorVariable(BaseModel):
    """This is used to store parameters used for indicator calculations.
    Essential, it's used to filter our a subset of all responses and assign it a name
    """
    name = models.CharField(max_length=150)
    description = models.TextField()
    indicator = models.ForeignKey(Indicator, related_name='variables')

    class Meta:
        app_label = 'survey'
        unique_together = ['name', 'indicator']


class IndicatorVariableCriteria(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    variable = models.ForeignKey(IndicatorVariable, related_name='criteria')
    # batch & parameter_list questions
    test_question = models.ForeignKey(Question, related_name='indicator_criteria', verbose_name='Filter')
    validation_test = models.CharField(max_length=200, choices=VALIDATION_TESTS, verbose_name='Condition')

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
        return method(value_key, *self.test_params, qs=queryset)


class IndicatorCriteriaTestArgument(BaseModel):
    criteria = models.ForeignKey(IndicatorVariableCriteria, related_name='arguments')
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'
