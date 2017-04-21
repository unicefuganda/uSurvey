from django.db import models
from survey.models.generics import TemplateQuestion


class QuestionTemplate(TemplateQuestion):
    module = models.ForeignKey(
        "QuestionModule",
        related_name="question_templates",
        null=True,
        blank=True)

    @classmethod
    def resolve_tag(cls):
        return 'question_library'

    class Meta:
        app_label = 'survey'
