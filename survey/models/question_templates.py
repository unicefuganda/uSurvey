from django.db import models
from survey.models.base import BaseModel
from survey.models.generics import GenericQuestion


class QuestionTemplate(GenericQuestion):
    module = models.ForeignKey(
        "QuestionModule", related_name="question_templates")

    class Meta:
        app_label = 'survey'


class TemplateOption(BaseModel):
    question = models.ForeignKey(
        QuestionTemplate, null=True, related_name="options")
    text = models.CharField(max_length=150, blank=False, null=False)
    order = models.PositiveIntegerField()

    @property
    def to_text(self):
        return "%d: %s" % (self.order, self.text)
