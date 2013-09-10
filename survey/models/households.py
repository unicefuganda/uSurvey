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
    PREVIOUS_PAGE_TEXT = "%s: Back" % getattr(settings,'USSD_PAGINATION',None).get('PREVIOUS')
    NEXT_PAGE_TEXT = "%s: Next" % getattr(settings,'USSD_PAGINATION',None).get('NEXT')

    class Meta:
        app_label = 'survey'

    def last_question_answered(self):
        answered = []
        for related_name in ['numericalanswer', 'textanswer', 'multichoiceanswer']:
            answer = getattr(self, related_name).all()
            if answer:answered.append(answer.latest())
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def next_question(self, last_question_answered=None):
        if not last_question_answered:
            last_question_answered = self.last_question_answered()

        investigator_location = self.investigator.location

        if not last_question_answered or not last_question_answered.is_in_open_batch(investigator_location):
            open_batch = Batch.currently_open_for(location=investigator_location)
            if open_batch:
                question = open_batch.first_question()
                return question
        else:
            return last_question_answered.next_question_for_household(self)

    def has_pending_survey(self):
        last_answered_question = self.last_question_answered()
        if not last_answered_question or not last_answered_question.next_question_for_household(self):
            return False
        else:
            return True

    def survey_completed(self):
        return not self.next_question()

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
        timeout = datetime.datetime.utcnow().replace(tzinfo=last_batch_completed_time.tzinfo) - datetime.timedelta(minutes=minutes)
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
        household_members = list(self.household_member.order_by('name').all())
        household_members.insert(0, self.head)
        return household_members

    def members_list(self, page=1):
        all_members = self.all_members()
        paginator = Paginator(all_members, self.MEMBERS_PER_PAGE)
        members = paginator.page(page)
        members_list = []
        for member in members:
            name = member.surname + " - (HEAD)" if isinstance(member, HouseholdHead) else member.name
            text = "%s: %s" % (all_members.index(member) + 1, name)
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


class HouseholdHead(BaseModel):
    household = models.OneToOneField(Household, null=True, related_name="head")
    surname = models.CharField(max_length=12, blank=False, null=True, verbose_name="Family Name")
    first_name = models.CharField(max_length=12, blank=False, null=True, verbose_name="Other Names")
    age = models.PositiveIntegerField(validators=[MinValueValidator(10), MaxValueValidator(99)], null=True)
    male = models.BooleanField(default=True, verbose_name="Gender")
    occupation = models.CharField(max_length=100, blank=False, null=False,
                                   verbose_name="Occupation / Main Livelihood", default="16")
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION,
                                          blank=False, default='Primary', verbose_name="Highest level of education completed")
    resident_since_year = models.PositiveIntegerField(validators=[MinValueValidator(1930), MaxValueValidator(2100)],
                                                         null=False, default=1984)
    resident_since_month = models.PositiveIntegerField(null=False, choices=MONTHS, blank=False, default=5)

    class Meta:
        app_label = 'survey'


class HouseholdMember(BaseModel):
    name = models.CharField(max_length=255)
    male = models.BooleanField(default=True, verbose_name="Sex")
    date_of_birth = models.DateField(auto_now=False)
    household = models.ForeignKey(Household,related_name='household_member')

    def get_member_groups(self):
        member_groups = []

        for group in HouseholdMemberGroup.objects.all():
            if group.belongs_to_group(self):
                member_groups.append(group)
        return member_groups

    def get_age(self):
        days_in_year = 365.2425
        return int((datetime.date.today() - self.date_of_birth).days/days_in_year)

    class Meta:
        app_label = 'survey'



