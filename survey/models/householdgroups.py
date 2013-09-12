from django.db import models
from survey.models.base import BaseModel

class HouseholdMemberGroup(BaseModel):
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(max_length=5, null=False, blank=False, unique=True, default=0)

    def all_questions(self):
        return self.question_group.all()

    def get_all_conditions(self):
        return self.conditions.all()

    def has_condition(self, household_member, condition):
        age = household_member.get_age()
        gender = household_member.male

        if condition.attribute.lower() == GroupCondition.GROUP_TYPES["AGE"].lower():
            condition_value = condition.matches_condition(age)
        else:
            condition_value = condition.matches_condition(gender)

        return condition_value

    def belongs_to_group(self, household_member):
        condition_match = []

        for condition in self.get_all_conditions():
            condition_match.append(self.has_condition(household_member, condition))

        return all(condition is True for condition in condition_match)

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
                'GENDER': 'GENDER'
    }

    value = models.CharField(max_length=50)
    attribute = models.CharField(max_length=20, default='AGE', choices=GROUP_TYPES.items())
    condition = models.CharField(max_length=20, default='EQUALS', choices=CONDITIONS.items())
    groups = models.ManyToManyField(HouseholdMemberGroup, related_name='conditions')

    def matches_condition(self, value):

        if self.condition == GroupCondition.CONDITIONS['EQUALS']:
            return str(self.value) == str(value)

        elif self.condition == GroupCondition.CONDITIONS['GREATER_THAN']:
            return value >= self.value

        elif self.condition == GroupCondition.CONDITIONS['LESS_THAN']:
            return value <= self.value

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return "%s > %s > %s" % (self.attribute, self.condition, self.value)
