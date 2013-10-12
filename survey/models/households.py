import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.datastructures import SortedDict
from rapidsms.contrib.locations.models import Location
from survey.investigator_configs import LEVEL_OF_EDUCATION, MONTHS
from survey.models.base import BaseModel
from survey.models.batch import Batch
from survey.models.investigator import Investigator
from django.conf import settings
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition
from django.core.paginator import Paginator


class Household(BaseModel):
    investigator = models.ForeignKey(Investigator, null=True, related_name="households")
    location = models.ForeignKey(Location, null=True)
    uid = models.PositiveIntegerField(blank=False, default=0, verbose_name="Household Unique Identification")

    MEMBERS_PER_PAGE = 4
    PREVIOUS_PAGE_TEXT = "%s: Back" % getattr(settings, 'USSD_PAGINATION', None).get('PREVIOUS')
    NEXT_PAGE_TEXT = "%s: Next" % getattr(settings, 'USSD_PAGINATION', None).get('NEXT')

    class Meta:
        app_label = 'survey'

    def get_head(self):
        household_head = None
        try:
            household_head = HouseholdHead.objects.get(household=self)
        except:
            pass
        return household_head

    def last_question_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer: answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def has_next_question(self, batch):
        for household_member in self.household_member.all():
            if not household_member.has_completed(batch):
                return True
        return False

    def has_pending_survey(self):
        for household_member in self.household_member.all():
            if household_member.pending_surveys():
                return True
        return False

    def survey_completed(self):
        batches = self.investigator.get_open_batch()
        for batch in batches:
            if self.has_next_question(batch):
                return False
        return True

    def retake_latest_batch(self):
        batches = self.investigator.get_open_batch()
        for batch in batches:
            questions = batch.all_questions()
            for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
                getattr(self, related_name).filter(question__in=questions).delete()

    def has_completed_batch(self, batch):
        return self.completed_batches.filter(batch=batch).count() > 0

    def has_completed_batches(self, batches):
        return self.completed_batches.filter(batch__in=batches).count() == len(batches)

    def batch_completed(self, batch):
        return self.completed_batches.get_or_create(household=self, investigator=self.investigator, batch=batch)

    def batch_reopen(self, batch):
        self.completed_batches.filter(household=self).delete()

    def can_retake_survey(self, batch, minutes):
        all_members = self.household_member.all()
        for member in all_members:
            if member.can_retake_survey(batch, minutes):
                return True
        return False

    def answers_for(self, questions):
        answers = []
        for question in questions:
            answer_class = question.answer_class()
            answer = answer_class.objects.filter(question=question, household=self)
            if answer:
                answer = answer[0]
                if question.is_multichoice():
                    option = answer.answer
                    answers.append(option.order)
                    answers.append(option.text)
                else:
                    answers.append(answer.answer)
            else:
                answers.append('')
        return answers

    def _get_related_location_name(self, key, location_hierarchy):
        location_object = location_hierarchy.get(key, None)

        location_name = ""

        if location_object:
            location_name = location_object.name

        return location_name

    def location_hierarchy(self):
        hierarchy = []
        location = self.location
        hierarchy.append([location.type.name, location])
        while location.tree_parent:
            location = location.tree_parent
            hierarchy.append([location.type.name, location])
        hierarchy.reverse()
        return SortedDict(hierarchy)

    def get_related_location(self):
        location_hierarchy = self.location_hierarchy()

        keys = ['District', 'County', 'Subcounty', 'Parish', 'Village']
        related_location = {}
        for key in keys:
            related_location[key] = self._get_related_location_name(key, location_hierarchy)

        return related_location

    def all_members(self):
        household_members = list(self.household_member.order_by('surname').filter(householdhead=None))
        household_members.insert(0, self.get_head())
        return household_members

    def completed_currently_open_batches(self):
        all_members = self.household_member.all()
        for member in all_members:
            if not member.survey_completed():
                return False
        return True

    def members_list(self, page=1):
        all_members = self.all_members()
        paginator = Paginator(all_members, self.MEMBERS_PER_PAGE)
        page = 1 if paginator.num_pages < page else page
        members = paginator.page(page)

        members_list = []
        for member in members:
            name = member.surname + " - (HEAD)" if isinstance(member, HouseholdHead) else member.surname
            text = "%s: %s" % (all_members.index(member) + 1, name)
            if member.survey_completed():
                text += "*"
            members_list.append(text)
        if members.has_previous():
            members_list.append(self.PREVIOUS_PAGE_TEXT)
        if members.has_next():
            members_list.append(self.NEXT_PAGE_TEXT)
        return "\n".join(members_list)


    @classmethod
    def set_related_locations(cls, households):
        for household in households:
            household.related_locations = household.get_related_location()
        return households

    @classmethod
    def next_uid(cls):
        all_households = Household.objects.filter()
        return (all_households.order_by('uid').reverse()[0].uid + 1) if all_households else 1


class HouseholdMember(BaseModel):
    surname = models.CharField(max_length=25, verbose_name="Family Name")
    first_name = models.CharField(max_length=25, blank=True, null=True, verbose_name="Other Names")
    male = models.BooleanField(default=True, verbose_name="Sex")
    date_of_birth = models.DateField(auto_now=False)
    household = models.ForeignKey(Household, related_name='household_member')

    def is_head(self):
        return len(HouseholdHead.objects.filter(householdmember_ptr_id=self.id)) > 0

    def get_location(self):
        return self.household.location

    def attribute_matches(self, condition):
        age = self.get_age()
        gender = self.male
        is_head = self.is_head()

        if condition.attribute.lower() == GroupCondition.GROUP_TYPES["AGE"].lower():
            condition_value = condition.matches_condition(age)
        elif condition.attribute.lower() == GroupCondition.GROUP_TYPES["GENDER"].lower():
            condition_value = condition.matches_condition(gender)
        else:
            condition_value = condition.matches_condition(is_head)
        return condition_value

    def belongs_to(self, member_group):
        condition_match = []
        for condition in member_group.get_all_conditions():
            condition_match.append(self.attribute_matches(condition))

        return all(condition is True for condition in condition_match)

    def get_member_groups(self, order_above=0):
        member_groups = []
        all_groups = HouseholdMemberGroup.objects.all().order_by('order')
        if order_above:
            all_groups = all_groups.filter(order__gte=order_above)

        for group in all_groups:
            if self.belongs_to(group):
                member_groups.append(group)

        return member_groups

    def get_age(self):
        days_in_year = 365.2425
        return int((datetime.date.today() - self.date_of_birth).days / days_in_year)

    def get_next_batch(self):
        open_ordered_batches = Batch.open_ordered_batches(self.get_location())

        for batch in open_ordered_batches:
            if batch.has_unanswered_question(self) and not self.completed_member_batches.filter(batch=batch):
                return batch
        return None

    def all_questions_answered(self, all_group_open_questions, batch):
        for question in all_group_open_questions:
            if question.answer_class().objects.filter(question=question, batch=batch,
                                                      householdmember=self).count() == 0:
                return False
        return True

    def last_question_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer and answer.filter(is_old=False): answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def has_answered(self, question, batch):
        answer_class = question.answer_class()
        return len(answer_class.objects.filter(question=question, householdmember=self, batch=batch, is_old=False)) > 0

    def next_unanswered_question_in(self, member_group, batch, order):
        all_questions = member_group.all_questions().filter(batches=batch, order__gte=order).order_by('order')
        for question in all_questions:
            if not self.has_answered(question, batch):
                return question
        return None

    def next_question(self, question, batch):
        member = self if not self.is_head() else self.get_member()
        answer = question.answer_class().objects.get(householdmember=member, question=question, batch=batch, is_old=False)
        try:
            return question.get_next_question_by_rule(answer, self.household.investigator)
        except ObjectDoesNotExist, e:
            return self.next_question_in_order(batch, question)

    def get_next_question_orders(self, last_question_answered):
        group_order = 0
        question_order = 0
        if not last_question_answered:
            last_question_answered = self.last_question_answered()

        if last_question_answered:
            if last_question_answered.subquestion:
                last_question_answered = last_question_answered.parent

            if last_question_answered.is_last_question_of_group():
                group_order = last_question_answered.group.order + 1
            else:
                question_order = last_question_answered.order
                group_order = last_question_answered.group.order

        return group_order, question_order

    def next_question_in_order(self, batch, last_question_answered=None):
        group_order, question_order = self.get_next_question_orders(last_question_answered)

        for member_group in self.get_member_groups(order_above=group_order):
            next_group_question = self.next_unanswered_question_in(member_group, batch, question_order)
            if next_group_question:
                return next_group_question
        return None

    def can_retake_survey(self, batch, minutes):
        if not batch:
            return False

        batch_completed_by_member = self.completed_member_batches.filter(batch=batch, householdmember=self,
                                                                         household=self.household)
        if batch_completed_by_member:
            last_batch_completed_time = batch_completed_by_member[0].created

            elapsed_seconds = (datetime.datetime.utcnow().replace(
                tzinfo=last_batch_completed_time.tzinfo) - last_batch_completed_time).seconds
            expected_timeout = minutes * 60

            if expected_timeout >= elapsed_seconds:
                return True
            return False
        return True

    def location(self):
        return self.household.location

    def batch_completed(self, batch):
        return self.completed_member_batches.get_or_create(householdmember=self, household=self.household,
                                                           investigator=self.household.investigator, batch=batch)

    def survey_completed(self):
        return self.get_next_batch() is None

    def has_started_the_survey(self):
        return bool(self.last_question_answered())

    def pending_surveys(self):
        return not (bool(self.survey_completed()) and bool(self.has_started_the_survey()))

    def has_open_batches(self):
        for batch in self.household.investigator.get_open_batch():
            if not self.completed_member_batches.filter(householdmember=self, household=self.household,
                                                        investigator=self.household.investigator, batch=batch):
                return True
        return False

    def has_completed(self, batch):
        for question in batch.all_questions().order_by('-order'):
            if not self.has_answered(question, batch):
                return False
        return True

    def mark_past_answers_as_old(self):
        self.completed_member_batches.all().delete()

        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answers = getattr(self, related_name).all()
            for answer in answers:
                answer.is_old = True
                answer.save()

    class Meta:
        app_label = 'survey'


class HouseholdHead(HouseholdMember):
    occupation = models.CharField(max_length=100, blank=False, null=False,
                                  verbose_name="Occupation / Main Livelihood", default="16")
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary',
                                          verbose_name="Highest level of education completed")
    resident_since_year = models.PositiveIntegerField(validators=[MinValueValidator(1930), MaxValueValidator(2100)],
                                                      null=False, default=1984)
    resident_since_month = models.PositiveIntegerField(null=False, choices=MONTHS, blank=False, default=5)

    class Meta:
        app_label = 'survey'

    def is_head(self):
        return True

    def get_member(self):
        return HouseholdMember.objects.get(householdhead=self)

