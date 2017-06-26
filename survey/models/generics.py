__author__ = 'anthony <>'
from model_utils.managers import InheritanceManager
from django.db import models
from survey.models.base import BaseModel
from survey.models.response_validation import ResponseValidation
from survey.models.interviews import Answer


class GenericQuestion(BaseModel):
    ANSWER_TYPES = [(name, name) for name in Answer.answer_types()]
    identifier = models.CharField(
        max_length=100, blank=False, null=True, verbose_name='Variable Name')
    text = models.CharField(max_length=150, blank=False, null=False,)
    answer_type = models.CharField(
        max_length=100, blank=False, null=False, choices=ANSWER_TYPES)
    response_validation = models.ForeignKey(ResponseValidation, related_name='%(class)s', null=True, blank=True,
                                            verbose_name='Validation Rule')

    @classmethod
    def type_name(cls):
        return cls._meta.verbose_name.title()

    class Meta:
        abstract = True

    def validators(self):
        return Answer.get_class(self.answer_type).validators()

    def validator_names(self):
        return [v.__name__ for v in Answer.get_class(self.answer_type).validators()]

    def odk_constraint(self):
        if self.response_validation:
            return self.response_validation.get_odk_constraint(self)

    def odk_constraint_msg(self):
        if self.response_validation:
            return self.response_validation.dconstraint_message


class TemplateQuestion(GenericQuestion):
    objects = InheritanceManager()

    class Meta:
        abstract = False


class TemplateOption(BaseModel):
    question = models.ForeignKey(
        TemplateQuestion,
        null=True,
        related_name="options")
    text = models.CharField(max_length=150, blank=False, null=False)
    order = models.PositiveIntegerField()

    @property
    def to_text(self):
        return "%d: %s" % (self.order, self.text)
