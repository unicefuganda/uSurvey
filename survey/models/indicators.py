import re
import pandas as pd
from asteval import Interpreter
from django.template import Template, Context
from django.db import models
from django.db.models import Count
from django.utils.datastructures import SortedDict
from survey.models.base import BaseModel
from survey.models.question_module import QuestionModule
from survey.models.interviews import MultiChoiceAnswer, Answer
from survey.models.surveys import Survey
from survey.models.batch import Batch
from survey.models.batch_questions import BatchQuestion
from survey.models.questions import Question, QuestionSet
from survey.models.interviews import Interview
from survey.models.locations import Location


class Indicator(BaseModel):
    REPORT_FIELD_NAME = '[IndicatorValue]'
    DECIMAL_PLACES = 2
    PERCENTAGE = 1
    COUNT = 2
    name = models.CharField(max_length=255, null=False)
    # module = models.ForeignKey(QuestionModule, null=False, related_name='indicator')
    description = models.TextField(null=True)
    survey = models.ForeignKey(Survey, related_name='indicators')
    question_set = models.ForeignKey(QuestionSet, related_name='indicators')
    display_on_dashboard = models.BooleanField(default=False)
    formulae = models.TextField()        # I'm allowing that the formula can contain long names
    # parameter = models.ForeignKey(BatchQuestion, related_name='indicators', null=True, blank=True)

    def __unicode__(self):
        return self.name

    @property
    def eqset(self):
        '''Returns the exactt question set for this indicator
        :return:
        '''
        return QuestionSet.get(id=self.question_set.id)

    def is_percentage_indicator(self):
        percentage_measure = [Indicator.MEASURE_CHOICES[0][1], Indicator.MEASURE_CHOICES[0][0]]
        return self.measure in percentage_measure

    def get_matching_interviews(self, batch, loc):
        pass

    def compute_for_next_location_type_in_the_hierarchy(self, current_location):
        locations = current_location.get_children()
        data = {}
        for location in locations:
            data[location] = self.compute_for_location(location)
        return data

    @classmethod
    def get_variables(cls, formulae):
        pattern = '{{ *([0-9a-zA-Z_]+) *}}'
        return set(re.findall(pattern, formulae))

    def active_variables(self):
        return Indicator.get_variables(self.formulae)

    def get_indicator_value(self, var_row, evaluator):
        math_string = Template(self.formulae).render(Context(var_row))
        result = evaluator(math_string)
        if len(evaluator.error) > 0:
            return None
        return round(result, self.DECIMAL_PLACES)

    def formulae_string(self):
        return Template(self.formulae).render(Context(dict([(name, name) for name in self.active_variables()])))

    def country_wide_value(self):
        country = Location.country()
        return self.get_data([country, ])['[IndicatorValue]'][0]

    def get_data(self, locations, *args, **kxargs):
        """Used to get the compute indicator values.
        :param locations: The locations of interest
        :param args:
        :param kxargs:
        :return:
        """
        tabulated_data = SortedDict()
        context = {}
        variable_names = self.active_variables()
        # options = self.parameter.options.order_by('order')
        # answer_class = Answer.get_class(self.parameter.answer_type)
        kwargs = {}
        report = {}
        for child_location in locations:
            target_locations = child_location.get_leafnodes(include_self=True)
            report[child_location.name] = [self.get_variable_value(target_locations,
                                                                   name) for name in variable_names]
        # for name in variable_names:
        #     report[name] = self.get_variable_aggregates(base_location, name)
        df = pd.DataFrame(report).transpose()
        if df.columns.shape[0] == len(variable_names):
            df.columns = variable_names
            # now include the formula results per location
            aeval = Interpreter()       # to avoid the recreating each time
            df[self.REPORT_FIELD_NAME] = df.apply(self.get_indicator_value, axis=1, args=(aeval, ))
        else:
            df = pd.DataFrame(columns=list(variable_names)+[self.REPORT_FIELD_NAME, ])
        return df

    def get_variable_aggregates(self, base_location, variable_name):
        variable = self.variables.get(name__iexact=variable_name)
        ikwargs = {'question_set__pk': self.question_set.id, 'survey': self.survey}
        parent_loc = 'ea__locations'
        for i in base_location.type.get_descendants(include_self=False):    # just to know how many levels down
            parent_loc = '%s__parent' % parent_loc
        ikwargs['%s__id' % parent_loc] = base_location.id
        valid_interviews = Interview.objects.filter(**ikwargs).values_list('id', flat=True)
        for criterion in variable.criteria.all():
            if criterion.test_question.answer_type == MultiChoiceAnswer.choice_name():
                value_key = 'as_value'
            else:
                value_key = 'as_text'
            kwargs = {
                'question__id': criterion.test_question.id,
                'interview__id__in': valid_interviews
            }
            valid_interviews = criterion.qs_passes_test(value_key, Answer.objects.filter(**kwargs).
                                                        only('interview__id').values_list('interview__id', flat=True))
        parent_loc = 'interview__%s__name' % parent_loc
        aggregate = valid_interviews.values(parent_loc).annotate(total=Count(parent_loc))
        return SortedDict([(d[parent_loc], d['total']) for d in aggregate])

    def get_variable_value(self, locations, variable_name):
        variable = self.variables.get(name__iexact=variable_name)
        valid_interviews = Interview.objects.filter(ea__locations__in=locations,
                                                    question_set__pk=self.question_set.id,
                                                    survey=self.survey,
                                                    ).values_list('id', flat=True)
        for criterion in variable.criteria.all():
            if criterion.test_question.answer_type == MultiChoiceAnswer.choice_name():
                value_key = 'as_value'
            else:
                value_key = 'as_text'
            kwargs = {
                'question__identifier__iexact': criterion.test_question.identifier,
                'interview__id__in': valid_interviews
            }
            valid_interviews = criterion.qs_passes_test(value_key, Answer.objects.filter(**kwargs).
                                                        only('interview__id').values_list('interview__id', flat=True))
        return valid_interviews.count()


class IndicatorVariable(BaseModel):
    """This is used to store parameters used for indicator calculations.
    Essential, it's used to filter our a subset of all responses and assign it a name
    """
    name = models.CharField(max_length=150)
    description = models.TextField()
    indicator = models.ForeignKey(Indicator, related_name='variables', null=True,
                                  blank=True)   # just to accomodate creation of
                                                                # variables then assigning them to indicators

    def __unicode__(self):
        return self.name

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
        test_args = [answer_class.prep_value(val) for val in self.test_params]
        method = getattr(Answer, 'fetch_%s' % self.validation_test, None)
        return method(value_key, *test_args, qs=queryset)


class IndicatorCriteriaTestArgument(BaseModel):
    criteria = models.ForeignKey(IndicatorVariableCriteria, related_name='arguments')
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'
