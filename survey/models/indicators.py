import re
import pandas as pd
from cacheops import cached_as
from asteval import Interpreter
from django.template import Template, Context
from django.db import models
from django.db.models import Count
from django.utils.datastructures import SortedDict
from survey.models.base import BaseModel
from survey.models.interviews import MultiChoiceAnswer, Answer
from survey.models.surveys import Survey
from survey.models.questions import Question, QuestionSet
from survey.models.interviews import Interview
from survey.models.locations import Location, LocationType


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
    # I'm allowing that the formula can contain long names
    formulae = models.TextField()
    # parameter = models.ForeignKey(BatchQuestion, related_name='indicators', null=True, blank=True)

    def __unicode__(self):
        return self.name

    @property
    def eqset(self):
        """Returns the exactt question set for this indicator
        :return:
        """
        return QuestionSet.get(id=self.question_set.id)

    def is_percentage_indicator(self):
        percentage_measure = [
            Indicator.MEASURE_CHOICES[0][1],
            Indicator.MEASURE_CHOICES[0][0]]
        return self.measure in percentage_measure

    def get_matching_interviews(self, batch, loc):
        pass

    def compute_for_next_location_type_in_the_hierarchy(
            self, current_location):
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
        return Template(self.formulae).render(
            Context(dict([(name, name) for name in self.active_variables()])))

    def country_wide_value(self):
        return self.country_wide_report()[self.REPORT_FIELD_NAME]

    def country_wide_report(self):
        country = Location.country()
        return self.get_data(country).transpose().to_dict()[country.name]

    def get_data(self, base_location, report_level=None):
        """Used to get the compute indicator values.
        :param locations: The locations of interest
        :param args:
        :param kxargs:
        :return:
        """
        if report_level is None:
            report_level = base_location.level

        @cached_as(self, base_location, extra=(report_level, ))
        def _get_data():
            SortedDict()
            variable_names = self.active_variables()
            # options = self.parameter.options.order_by('order')
            # answer_class = Answer.get_class(self.parameter.answer_type)
            report = {}
            if report_level <= base_location.level:
                location_names = [base_location.name, ]
            else:
                location_names = base_location.get_descendants().filter(level=report_level).values_list('name',
                                                                                                        flat=True)
            df = pd.DataFrame(columns=list(location_names))
            for variable_name in variable_names:
                # better to make variable_name the index
                df = df.append(pd.DataFrame([self.get_variable_aggregates(base_location, variable_name,
                                                                          report_level=report_level), ],
                                            index=[variable_name, ],
                                            columns=list(location_names)))
            df = df.transpose()
            if df.columns.shape[0] == len(variable_names):
                df.columns = variable_names
                # now include the formula results per location
                aeval = Interpreter()       # to avoid the recreating each time
                df[self.REPORT_FIELD_NAME] = df.apply(self.get_indicator_value, axis=1, args=(aeval, ))
            return df
        return _get_data()

    def get_variable_aggregates(self, base_location, variable_name, report_level=1):
        variable = self.variables.get(name__iexact=variable_name)
        return variable.get_variable_aggregates(base_location, report_level=report_level)

    def get_variable_value(self, locations, variable_name):
        variable = self.variables.get(name__iexact=variable_name)
        return variable.get_valid_qs(locations).count()


class IndicatorVariable(BaseModel):
    """This is used to store parameters used for indicator calculations.
    Essential, it's used to filter our a subset of all responses and assign it a name
    """
    name = models.CharField(max_length=150)
    description = models.TextField()
    indicator = models.ForeignKey(
        Indicator,
        related_name='variables',
        null=True,
        blank=True)  # just to accomodate creation of
    # variables then assigning them to indicators

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'survey'
        unique_together = ['name', 'indicator']

    def get_valid_qs(self, locations):
        """Return the queryset valid according to this indicator variable
        :param locations:
        :return:
        """
        indicator = self.indicator
        ikwargs = {'ea__locations__in': locations,
                   'question_set__pk': indicator.question_set.pk,
                   'survey__pk': indicator.survey.pk}
        interviews = Interview.objects.filter(**ikwargs)
        for criterion in self.criteria.all():
            kwargs = dict()
            kwargs['answer__question__identifier__iexact'] = criterion.test_question.identifier
            # be careful here regarding multiple validation tests with same name (e.g a__gt=2, a__gt=10)
            kwargs.update(Answer.get_validation_queries(criterion.validation_test, 'as_value',
                                                        namespace='answer__', *criterion.prepped_args))
            interviews = interviews.filter(**kwargs)
        return interviews.distinct('id')

    def get_variable_aggregates(self, base_location, report_level=1):
        indicator = self.indicator
        ikwargs = {'question_set__pk': indicator.question_set.pk,
                   'survey__pk': indicator.survey.pk}
        parent_loc = 'ea__locations'
        hierachy_count = Location.country().type.get_descendant_count()
        for i in range(hierachy_count - report_level):    # fetches direct descendants from ea__locs
            parent_loc = '%s__parent' % parent_loc
        # exploiting mptt artributes to speed up this query
        lowest_level = base_location.type.get_descendants(include_self=False).last().level
        left = base_location.lft
        right = base_location.rght
        if report_level <= base_location.level:     # if you want to include base_location (anything above becomes self
            left += 1
            right -= 1
        ikwargs.update({'ea__locations__lft__gte': left, 'ea__locations__lft__lte': right,
                        'ea__locations__level': lowest_level})
        interviews = Interview.objects.filter(**ikwargs)
        for criterion in self.criteria.all():
            kwargs = dict()
            kwargs['answer__question__identifier__iexact'] = criterion.test_question.identifier
            # be careful here regarding multiple validation tests with same name (e.g a__gt=2, a__gt=10)
            kwargs.update(Answer.get_validation_queries(criterion.validation_test, 'as_value',
                                                        namespace='answer__', *criterion.prepped_args))
            interviews = interviews.filter(**kwargs)
        parent_loc = '%s__name' % parent_loc
        return dict(interviews.values_list(parent_loc).annotate(total=Count('id', distinct=True)))


class IndicatorVariableCriteria(BaseModel):
    """A variable is essential a filtered set of answers. Hence they need the filter criteria to be defined.
    This is the purpose of this class
    """
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    variable = models.ForeignKey(IndicatorVariable, related_name='criteria')
    # batch & parameter_list questions
    test_question = models.ForeignKey(
        Question,
        related_name='indicator_criteria',
        verbose_name='Filter')
    validation_test = models.CharField(
        max_length=200,
        choices=VALIDATION_TESTS,
        verbose_name='Condition')

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
        return IndicatorCriteriaTestArgument.objects.filter(
            criteria=self).order_by('position')

    @property
    def prepped_args(self):
        answer_class = Answer.get_class(self.test_question.answer_type)
        return [answer_class.prep_value(val) for val in self.test_params]

    def qs_passes_test(self, value_key, queryset):
        test_args = self.prepped_args
        method = getattr(Answer, 'fetch_%s' % self.validation_test, None)
        return method(value_key, *test_args, qs=queryset)


class IndicatorCriteriaTestArgument(BaseModel):
    criteria = models.ForeignKey(
        IndicatorVariableCriteria,
        related_name='arguments')
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'
