__author__ = 'anthony <>'
from django.db import models
from survey.models.questions import Question
from survey.models.respondents import RespondentGroup, SurveyParameterList


class BatchQuestion(Question):
    group = models.ForeignKey(RespondentGroup, related_name='questions', null=True, blank=True,
                              on_delete=models.SET_NULL)
    module = models.ForeignKey(
        "QuestionModule", related_name="questions", default='', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        new_group = False
        # check if this group has been previously assigned to this Question set.
        if self.group and RespondentGroup.objects.filter(questions__qset__id=self.qset.id, id=self.group.id).exists():
            new_group = True
        instance = super(BatchQuestion, self).save(*args, **kwargs)
        # if this group is new for this batch, refresh the parameter list
        if new_group:       # if new group has been introduced, update the parameter list
            SurveyParameterList.update_parameter_list(self)
        return instance

