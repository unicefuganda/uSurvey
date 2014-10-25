from survey.models import RandomHouseHoldSelection, Survey
from survey.ussd.household_selection import HouseHoldSelection
from survey.ussd.ussd_survey import USSDSurvey
from survey.views.ussd_base_view import USSDBaseView


class USSDPremenu(object):

    def __init__(self, investigator, params):
        self.investigator = investigator
        self.params = params
        self.open_survey = Survey.currently_open_survey(self.investigator.location)

    def _finished_segmentation(self):
        random_household_selection = RandomHouseHoldSelection.objects.filter(mobile_number=self.investigator.mobile_number,
                                                                             survey=self.open_survey)
        return random_household_selection.exists() and self.investigator.households.exists()

    def respond(self):
        if not self.open_survey:
            return {'action': USSDSurvey.ACTIONS['END'], 'responseString': USSDSurvey.MESSAGES['NO_OPEN_BATCH']}

        if not self._finished_segmentation():
            return self._render_selection()

        return self._render_survey()

    def _render_selection(self):
        return HouseHoldSelection(self.investigator.mobile_number, self.params).response(self.open_survey)

    def _render_survey(self):
        return USSDBaseView(self.investigator, self.params).response()