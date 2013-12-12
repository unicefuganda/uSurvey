from django.utils.datastructures import SortedDict
from survey.models import MultiChoiceAnswer, Household


class SimpleIndicatorService(object):
    def __init__(self, formula, location_parent):
        self.question = formula.count
        self.survey = formula.indicator.batch.survey
        self.location_parent = location_parent

    def hierarchical_count(self):
        return self.hierarchical_count_for(self.location_parent)

    def hierarchical_count_for(self, location_parent):
        locations = location_parent.get_children().order_by('name')[:10]
        answers = MultiChoiceAnswer.objects.filter(question=self.question)
        return self._format_answer(locations, answers)

    def _format_answer(self, locations, answers):
        question_options = self.question.options.all()
        data = SortedDict()
        for location in locations:
            households = Household.all_households_in(location, self.survey)
            data[location] = {option.text: answers.filter(answer=option, household__in=households).count() for option in
                              question_options}
        return data

    def get_location_names_and_data_series(self):
        options, locations_names = self._arrange_answers_per_options()
        data_series = self.to_high_chart_format(options)
        return data_series, locations_names

    def _arrange_answers_per_options(self):
        options = {}
        locations_names = []
        for location, answers in (self.hierarchical_count()).items():
            locations_names.append(str(location.name))
            for option, answer in answers.items():
                if not options.has_key(option):
                    options[option] = []
                options[option].append(answer)
        return options, locations_names

    @classmethod
    def to_high_chart_format(cls, options):
        data_series = []
        for key, value in options.items():
            data_series.append(SortedDict({
                'name': str(key),
                'data': value
            }))
        return data_series

    def tabulated_data_series(self):
        tabulated_data = []
        first_level_locations = self.location_parent.get_children().order_by('name')[:10]
        for location in first_level_locations:
            for child_location, answers in self.hierarchical_count_for(location).items():
                tab_data = SortedDict({location.type.name: location.name,
                                       child_location.type.name: child_location.name})
                tab_data.update(answers)
                tab_data.update({'Total': sum(answers.values())})
                tabulated_data.append(tab_data)
        return tabulated_data
