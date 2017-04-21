__author__ = 'anthony <>'
from django.db import models
from survey.models.questions import Question
from survey.models.respondents import RespondentGroup, SurveyParameterList


class BatchQuestion(Question):
    group = models.ForeignKey(
        RespondentGroup,
        related_name='questions',
        null=True,
        blank=True,
        on_delete=models.SET_NULL)
    module = models.ForeignKey(
        "QuestionModule",
        related_name="questions",
        default='',
        on_delete=models.SET_NULL,
        null=True,
        blank=True)

    def save(self, *args, **kwargs):
        instance = super(BatchQuestion, self).save(*args, **kwargs)
        update_parameter_list(self)
        return instance


def update_parameter_list(batch_question):
    # check if this group has been previously assigned to this Question set.
    from survey.models import Batch
    if batch_question.group and RespondentGroup.objects.filter(
            questions__qset__id=batch_question.qset.id,
            id=batch_question.group.id).exists():
        SurveyParameterList.update_parameter_list(
            Batch.get(pk=batch_question.qset.pk))
