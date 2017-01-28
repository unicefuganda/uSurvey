from survey.models.base import BaseModel
from django.db import models
from survey.models.question_module import QuestionModule
from survey.models.interviews import MultiChoiceAnswer, Answer
from survey.models.surveys import Survey
from survey.models.questions import Question


class Indicator(BaseModel):
    name = models.CharField(max_length=255, null=False)
    target_group = models.ForeignKey('Group', related_name='indicators', null=True, blank=True)
    module = models.ForeignKey(QuestionModule, null=False, related_name='indicator')
    description = models.TextField(null=True)
    # disabling this in preference to show indicator
    # measure = models.CharField(max_length=255, null=False, choices=MEASURE_CHOICES, default=MEASURE_CHOICES[0][1])
    batch = models.ForeignKey("Batch", null=True, related_name='indicators')


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

    # def compute_for_location(self, location):
    #     interviewers = Interviewer.lives_under_location(location)
    #     if self.numerator.is_multichoice():
    #         return self.compute_multichoice_question_for_interviewers(interviewers)
    #     else:
    #         return self.compute_numerical_question_for_interviewers(interviewers)
