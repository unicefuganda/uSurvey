from django.db import models
from django.utils.datastructures import SortedDict
from survey.models.base import BaseModel


class HouseholdMemberGroup(BaseModel):
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(max_length=5, null=False, blank=False, unique=True, default=0)
    
    def __unicode__(self):
        return self.name

    def all_questions(self):
        return self.question_group.all()

    def get_all_conditions(self):
        return self.conditions.all()

    def maximum_question_order(self):
        all_questions = self.all_questions()
        return all_questions.order_by('order').reverse()[0].order if all_questions else 0

    def remove_related_questions(self):
        self.question_group.clear()

    def household_members_count_per_location_in(self, locations, survey):
        data = SortedDict()
        all_households = survey.survey_household.all()
        from survey.models import HouseholdMember
        for location in locations:
            location_descendants = location.get_descendants(include_self=True).values_list('id', flat=True)
            households = all_households.filter(ea__locations__in=location_descendants).values_list('id', flat=True)
            all_members = HouseholdMember.objects.filter(household__id__in=households).select_subclasses()
            qualified_members = filter(lambda member: member.belongs_to(self), all_members)
            data[location] = {self.name: len(qualified_members)}
        return data

    def hierarchical_result_for(self, location_parent, survey):
        locations = location_parent.get_children().order_by('name')[:10]
        answers = self.household_members_count_per_location_in(locations, survey)
        return answers

    @classmethod
    def max_order(cls):
        all_groups = cls.objects.all()
        return all_groups.order_by('-order')[0].order if all_groups else 0

    class Meta:
        app_label = 'survey'


def household_member_test(func):
    func.is_reply_test = True
    return func

class GroupCondition(BaseModel):
    CONDITIONS = {
        'EQUALS': 'EQUALS',
        'GREATER_THAN': 'GREATER_THAN',
        'LESS_THAN': 'LESS_THAN',
    }

    MATCHING_METHODS = {
            'EQUALS': 'is_equal',
            'GREATER_THAN': 'is_greater_than',
            'LESS_THAN': 'is_less_than',
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

    def matches(self, attributes):
        value = attributes.get(self.attribute.upper())
        return self.matches_condition(value)

    def matches_condition(self, value):
        method = getattr(self, self.MATCHING_METHODS[self.condition])
        return method(value)

    def is_equal(self, value):
        return str(self.value) == str(value) or str(value) == str(self.confirm_male(self.value))

    def is_greater_than(self, value):
        return int(value) >= int(self.value)

    def is_less_than(self, value):
        return int(value) <= int(self.value)

    class Meta:
        app_label = 'survey'
        unique_together = ('value', 'attribute', 'condition')

    def __unicode__(self):
        return "%s %s %s" % (self.attribute, self.condition, self.value)
