from survey.models import Household


class BatchCompletionRates:
    def __init__(self, batch):
        self.batch = batch

    def calculate_percent(self, numerator, denominator):
        try:
            return numerator * 100 / denominator
        except ZeroDivisionError:
            return 0

    def percent_completed_households(self, location):
        all_households = Household.all_households_in(location)
        return self.percentage_completed(all_households)

    def percentage_completed(self, all_households):
        completed_households = filter(lambda household: household.has_completed_batch(self.batch), all_households)
        return self.calculate_percent(len(completed_households), all_households.count())


class BatchLocationCompletionRates(BatchCompletionRates):
    def __init__(self, batch, location):
        self.batch = batch
        self.location = location
        self.all_households = Household.all_households_in(self.location)

    def percent_completed_households(self):
        all_households = self.all_households
        completed_households = filter(lambda household: household.has_completed_batch(self.batch), all_households)
        return self.calculate_percent(len(completed_households), all_households.count())
        #
        # percent = super(BatchLocationCompletionRates, self).percentage_completed(self.all_households)
        # return percent

    def interviewed_households(self):
        _interviewed_households=[]
        for household in self.all_households:
            attributes= {'household':household,
                         'date_interviewed':household.date_interviewed_for(self.batch),
                         'number_of_member_interviewed':len(household.members_interviewed(self.batch)),}
            _interviewed_households.append(attributes)
        return _interviewed_households


class BatchHighLevelLocationsCompletionRates(BatchCompletionRates):
    def __init__(self, batch, locations):
        self.batch = batch
        self.locations = locations

    def attributes(self):
        _completion_rates =[]
        for location in self.locations:
            attribute ={}
            attribute['location'] = location
            attribute['total_households'] = Household.all_households_in(location).count()
            attribute['completed_households_percent'] = self.percent_completed_households(location)
            _completion_rates.append(attribute)

        return _completion_rates
