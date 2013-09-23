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
        is_head = household_member.is_head()

        if condition.attribute.lower() == GroupCondition.GROUP_TYPES["AGE"].lower():
            condition_value = condition.matches_condition(age)
        elif condition.attribute.lower() == GroupCondition.GROUP_TYPES["GENDER"].lower():
            condition_value = condition.matches_condition(gender)
        else:
            condition_value = condition.matches_condition(is_head)
        return condition_value

    def all_questions_answered(self, member):
        last_question = self.last_question()
        if last_question:
            answer_class = last_question.answer_class()
            answered_question = answer_class.objects.filter(question=last_question, householdmember=member)
            return len(answered_question) > 0
        return True

    def first_question(self, member):
        all_questions = self.all_questions().order_by('order')

        open_questions = filter(lambda question: question.is_in_open_batch(member.get_location()), all_questions) if all_questions else None

        if open_questions:
            return open_questions[0]
        else:
            return None

    def all_unanswered_open_batch_questions(self, member, batch):
        all_questions = self.all_questions().filter(batch=batch).order_by('order')
        open_batch_questions = []

        for question in all_questions:
            if batch.is_open_for(member.get_location()) and not question.has_been_answered(member):
                open_batch_questions.append(question)

        return open_batch_questions

    def last_question(self):
        all_questions = self.all_questions().exclude(order=None)
        return all_questions.order_by('order').reverse()[0] if all_questions else None

    def belongs_to_group(self, household_member):
        condition_match = []

        for condition in self.get_all_conditions():
            condition_match.append(self.has_condition(household_member, condition))

        return all(condition is True for condition in condition_match)

    def maximum_question_order(self):
        all_questions = self.all_questions()
        return all_questions.order_by('order').reverse()[0].order if all_questions else 0

    def get_next_question_for(self, member, last_question=None):
        if not last_question:
            last_question = member.last_question_answered()

        if last_question and last_question.group == self:
            try:
                order = last_question.parent.order if last_question.subquestion else last_question.order
                last_question = self.all_questions().get(order=order + 1)
            except:
                return None
            return last_question if last_question.is_in_open_batch(member.get_location()) else self.get_next_question_for(member, last_question)

        return self.all_questions().order_by('order')[0]

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
        return  str(value).lower() == "male" or (str(value).lower() == "head" and self.attribute == GroupCondition.GROUP_TYPES['GENERAL'])

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
        return "%s > %s > %s" % (self.attribute, self.condition, self.value)
