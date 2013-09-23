import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from survey.investigator_configs import LEVEL_OF_EDUCATION, MONTHS
from survey.models.base import BaseModel
from survey.models.batch import Batch
from survey.models.investigator import Investigator
from django.conf import settings
from survey.models.householdgroups import HouseholdMemberGroup
from django.core.paginator import Paginator


class Household(BaseModel):
    investigator = models.ForeignKey(Investigator, null=True, related_name="households")
    uid = models.PositiveIntegerField(blank=False, default=0, unique=True,
                                      verbose_name="Household Unique Identification")

    MEMBERS_PER_PAGE = 4
    PREVIOUS_PAGE_TEXT = "%s: Back" % getattr(settings, 'USSD_PAGINATION', None).get('PREVIOUS')
    NEXT_PAGE_TEXT = "%s: Next" % getattr(settings, 'USSD_PAGINATION', None).get('NEXT')

    class Meta:
        app_label = 'survey'

    def get_head(self):
        return HouseholdHead.objects.get(household=self)

    def last_question_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer: answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def has_next_question(self):
        for household_member in self.household_member.all():
            if household_member.next_question():
                return True
        return False

    def has_pending_survey(self):
        for household_member in self.household_member.all():
            if household_member.pending_surveys():
                return True
        return False


    def survey_completed(self):
        return not self.has_next_question()

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
        last_batch_completed_time = self.completed_batches.filter(batch=batch, household=self)[0].created
        timeout = datetime.datetime.utcnow().replace(tzinfo=last_batch_completed_time.tzinfo) - datetime.timedelta(
            minutes=minutes)
        return last_batch_completed_time >= timeout

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

    def get_related_location(self):
        location_hierarchy = self.investigator.location_hierarchy()

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


class HouseholdMember(BaseModel):
    surname = models.CharField(max_length=25, verbose_name="Family Name")
    first_name = models.CharField(max_length=25, blank=True, null=True, verbose_name="Other Names")
    male = models.BooleanField(default=True, verbose_name="Sex")
    date_of_birth = models.DateField(auto_now=False)
    household = models.ForeignKey(Household, related_name='household_member')

    def is_head(self):
        return False

    def get_location(self):
        investigator = self.household.investigator
        return investigator.location if investigator else None

    def get_member_groups(self):
        member_groups = []
        for group in HouseholdMemberGroup.objects.all().order_by('order'):
            if group.belongs_to_group(self):
                member_groups.append(group)
        return member_groups

    def get_age(self):
        days_in_year = 365.2425
        return int((datetime.date.today() - self.date_of_birth).days / days_in_year)

    def get_next_group(self, batch):
        member_groups = self.get_member_groups()

        for member_group in member_groups:
            all_group_open_questions = member_group.all_unanswered_open_batch_questions(self, batch)
            if all_group_open_questions and not self.all_questions_answered(all_group_open_questions):
                return member_group

    def get_next_batch(self):
        open_batches = Batch.open_batches(self.get_location())
        for batch in open_batches:
            if batch.has_unanswered_question(self) and not self.completed_member_batches.filter(batch=batch):
                return batch
        return None

    def all_questions_answered(self, all_group_open_questions):
        for question in all_group_open_questions:
            if len(question.answer_class().objects.filter(question=question, batch=question.batch, householdmember=self)) == 0:
                return False
        return True

    def last_question_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer: answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def next_question(self, last_question_answered=None):
        next_batch = self.get_next_batch()

        if not next_batch:
            return None

        next_group = self.get_next_group(next_batch)

        next_group_questions = next_group.all_unanswered_open_batch_questions(self, next_batch)

        return next_group_questions[0]

    def can_retake_survey(self, batch, minutes):
        completed_batches_by_member = self.completed_member_batches.filter(batch=batch, householdmember=self)
        if completed_batches_by_member:
            last_batch_completed_time = completed_batches_by_member[0].created
            timeout = datetime.datetime.utcnow().replace(tzinfo=last_batch_completed_time.tzinfo) - datetime.timedelta(
                minutes=minutes)
            return last_batch_completed_time >= timeout

        return True

    def batch_completed(self, batch):
        return self.completed_member_batches.get_or_create(householdmember=self, household=self.household,
                                                           investigator=self.household.investigator, batch=batch)

    def survey_completed(self):
        return (self.get_next_batch() is None)

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

