from django.utils.datastructures import SortedDict


class SimpleIndicatorService(object):
    def __init__(self, formula, location_parent):
        # import pdb; pdb.set_trace()
        self.count = formula.get_count_type()
        self.survey = formula.indicator.batch.survey
        self.location_parent = location_parent

    def hierarchical_count(self):
        return self.hierarchical_count_for(self.location_parent)

    def hierarchical_count_for(self, location_parent):
        return self.count.hierarchical_result_for(location_parent, self.survey)

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
                tab_data = SortedDict({location.type.name: location.name})
                tab_data[child_location.type.name] = child_location.name
                tab_data.update(answers)
                tab_data.update({'Total': sum(answers.values())})
                tabulated_data.append(tab_data)
        return tabulated_data
