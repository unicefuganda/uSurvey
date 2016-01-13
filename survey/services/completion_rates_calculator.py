from survey.models import Location
from survey.models import Household


class BatchCompletionRates:
    def __init__(self, batch):
        self.batch = batch

    def calculate_percent(self, numerator, denominator):
        try:
            return numerator * 100 / denominator
        except ZeroDivisionError:
            return 0

    def percent_completed_households(self, location, survey, ea=None):
        all_households = Household.all_households_in(location, survey, ea)
        return self.percentage_completed(all_households)

    def percentage_completed(self, all_households):
        completed_households = filter(lambda household: household.has_completed_batch(self.batch), all_households)
        return self.calculate_percent(len(completed_households), all_households.count())


class BatchLocationCompletionRates(BatchCompletionRates):
    def __init__(self, batch, location=None, ea=None, specific_households=None):
        self.batch = batch
        self.ea = ea
        self.location = location
        if specific_households:
            self.all_households = Household.objects.filter(pk__in=specific_households)
        else:
            self.all_households = Household.all_households_in(self.location, batch.survey, ea)

    def percent_completed_households(self):
        all_households = self.all_households
        completed_households = filter(lambda household: household.has_completed_batch(self.batch), all_households)
        return self.calculate_percent(len(completed_households), all_households.count())

    def interviewed_households(self):
        _interviewed_households = []
        for household in self.all_households:
            attributes = {'household': household,
                          'date_interviewed': household.date_interviewed_for(self.batch),
                          'number_of_member_interviewed': household.total_members_interviewed(self.batch)}
            _interviewed_households.append(attributes)
        return _interviewed_households


class BatchHighLevelLocationsCompletionRates(BatchCompletionRates):
    def __init__(self, batch, locations, ea=None):
        self.batch = batch
        self.locations = locations
        self.ea = ea

    def attributes(self):
        _completion_rates =[]
        for location in self.locations:
            attribute = {'location': location,
                         'total_households': Household.all_households_in(location, self.batch.survey, self.ea).count(),
                         'completed_households_percent': self.percent_completed_households(location, self.batch.survey, self.ea)}
            _completion_rates.append(attribute)
        return _completion_rates

class BatchSurveyCompletionRates:
    def __init__(self, location_type):
        self.location_type = location_type
        self.locations = Location.objects.filter(type=location_type)

    def get_completion_formatted_for_json(self, survey):
        all_batches = survey.batches.all()
        completion_rates_dict = {}
        number_of_batches = len(all_batches)

        for location in self.locations:
            percent_completed = 0.0
            percent_completed = reduce(lambda percent_completed, rate: percent_completed + rate,
                                       map(lambda batch: BatchLocationCompletionRates(batch, location).percent_completed_households(), all_batches))
            completion_rates_dict[location.name.upper()] = percent_completed/number_of_batches #if survey.is_open_for(location) else -1
        return completion_rates_dict
