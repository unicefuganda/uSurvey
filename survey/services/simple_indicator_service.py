from rapidsms.contrib.locations.models import Location
from survey.models import MultiChoiceAnswer, Household


class SimpleIndicatorService(object):
    def __init__(self, formula, location_parent):
        self.question = formula.count
        self.survey = formula.indicator.batch.survey
        self.location_parent = location_parent

    def hierarchical_count(self):
        locations = Location.objects.filter(tree_parent=self.location_parent)
        answers = MultiChoiceAnswer.objects.filter(question=self.question)
        return self._format_answer(locations, answers)

    def _format_answer(self, locations, answers):
        question_options = self.question.options.all()
        data = {}
        for location in locations:
            households = Household.all_households_in(location, self.survey)
            data[location] = {option.text: answers.filter(answer=option, household__in=households).count() for option in question_options}
        return data