from django.db import models
from survey.models.base import BaseModel


class HouseholdMemberGroup(BaseModel):
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(max_length=5, null=False, blank=False, unique=True, default=0)

    def all_questions(self):
        return self.question_group.all()

    def get_all_conditions(self):
        return self.conditions.all()

    def last_question(self):
        all_questions = self.all_questions().exclude(order=None)
        return all_questions.order_by('order').reverse()[0] if all_questions else None

    def maximum_question_order(self):
        all_questions = self.all_questions()
        return all_questions.order_by('order').reverse()[0].order if all_questions else 0

    def remove_related_questions(self):
        self.question_group.clear()

    @classmethod
    def max_order(cls):
        all_groups = cls.objects.all()
        return all_groups.order_by('-order')[0].order if all_groups else 0

    class Meta:
        app_label = 'survey'


class GroupCondition(BaseModel):
    CONDITIONS = {
        'EQUALS': 'EQUALS',
        'GREATER_THAN': 'GREATER_THAN',
        'LESS_THAN': 'LESS_THAN',
    }

    GROUP_TYPES = {
        'AGE': 'AGE',
        'GENDER': 'GENDER',
        'GENERAL': 'GENERAL'
    }

    value = models.CharField(max_length=50)
    attribute = models.CharField(max_length=20, default='AGE', choices=GROUP_TYPES.items())
    condition = models.CharField(max_length=20, default='EQUALS', choices=CONDITIONS.items())
    groups = models.ManyToManyField(HouseholdMemberGroup, related_name='conditions')

    def confirm_male(self, value):
        if str(value) == str(True) or str(value) == str(False):
            return value
        return str(value).lower() == "male" or (str(value).lower() == "head" and self.attribute == GroupCondition.GROUP_TYPES['GENERAL'])

    def matches_condition(self, value):
        if self.condition == GroupCondition.CONDITIONS['EQUALS']:
            return str(self.value) == str(value) or str(value) == str(self.confirm_male(self.value))

        elif self.condition == GroupCondition.CONDITIONS['GREATER_THAN']:
            return int(value) >= int(self.value)

        elif self.condition == GroupCondition.CONDITIONS['LESS_THAN']:
            return int(value) <= int(self.value)

    class Meta:
        app_label = 'survey'
        unique_together = ('value', 'attribute', 'condition')

    def __unicode__(self):
        return "%s %s %s" % (self.attribute, self.condition, self.value)
