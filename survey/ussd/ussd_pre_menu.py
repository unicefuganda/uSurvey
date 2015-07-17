from survey.models import Survey
from survey.ussd.household_selection import HouseHoldSelection
from survey.ussd.ussd_survey import USSDSurvey
from survey.views.ussd_base_view import USSDBaseView


class USSDPremenu(object):

    def __init__(self, interviewer, params):
        self.interviewer = interviewer
        self.params = params
        self.open_survey = Survey.currently_open_survey(self.interviewer.location)

    def _finished_segmentation(self):
        pass

    def respond(self):
        if not self.open_survey:
            return {'action': USSDSurvey.ACTIONS['END'], 'responseString': USSDSurvey.MESSAGES['NO_OPEN_BATCH']}

        if not self._finished_segmentation():
            return self._render_selection()

        return self._render_survey()

    def _render_selection(self):
        return HouseHoldSelection(self.interviewer.mobile_number, self.params).response(self.open_survey)

    def _render_survey(self):
        return USSDBaseView(self.interviewer, self.params).response()