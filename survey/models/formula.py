from django.db import models
from django.db.models import Sum
from survey.models.base import BaseModel
from survey.models.interviewer import Interviewer
from survey.models.questions import Question, QuestionOption


class Formula(BaseModel):
    numerator = models.ForeignKey(Question, null=True, related_name="as_numerator")
    groups = models.ForeignKey("HouseholdMemberGroup", null=True, blank=True, related_name="as_group")
    denominator = models.ForeignKey(Question, null=True, blank=True, related_name="as_denominator")
    numerator_options = models.ManyToManyField(QuestionOption, null=True, blank=True, related_name='numerator_options')
    denominator_options = models.ManyToManyField(QuestionOption, null=True, blank=True, related_name='denominator_options')
    count = models.ForeignKey(Question, null=True, blank=True, related_name="as_count")
    indicator = models.ForeignKey("Indicator", null=True, related_name="formula")

    class Meta:
        app_label = 'survey'

    def get_count_type(self):
        return self.count or self.groups

    def compute_for_location(self, location):
        interviewers = Interviewer.lives_under_location(location)
        if self.numerator.is_multichoice():
            return self.compute_multichoice_question_for_interviewers(interviewers)
        else:
            return self.compute_numerical_question_for_interviewers(interviewers)

    def compute_for_next_location_type_in_the_hierarchy(self, current_location):
        locations = current_location.get_children()
        data = {}
        for location in locations:
            data[location] = self.compute_for_location(location)
        return data

    def compute_numerical_question_for_interviewers(self, interviewers):
        values = []
        for interviewer in interviewers:
            values.append(self.compute_numerical_question_for_interviewer(interviewer))
        return sum(values) / len(values)

    def compute_multichoice_question_for_interviewers(self, interviewers):
        values = []
        computed_dict = {}
        for interviewer in interviewers:
            values.append(self.compute_multichoice_question_for_interviewer(interviewer))

        denominator = len(values)
        for option in self.numerator.options.all():
            numerator = sum([value[option.text] for value in values])
            computed_dict[option.text] = numerator / denominator
        return computed_dict

    def process_formula(self, numerator, denominator, interviewer):
        return ((numerator * interviewer.weights) / denominator) * 100

    def compute_multichoice_question_for_interviewer(self, interviewer):
        values = {}
        denominator = self.answer_sum_for_interviewer(self.denominator, interviewer)
        for option in self.numerator.options.all():
            numerator = self.compute_numerator_for_option(option, interviewer)
            values[option.text] = self.process_formula(numerator, denominator, interviewer)
        return values

    def compute_numerator_for_option(self, option, interviewer):
        households = self.numerator.answer_class().objects.filter(interviewer=interviewer, answer=option).values_list(
            'household', flat=True)
        return \
            self.denominator.answer_class().objects.filter(household__in=households,
                                                           question=self.denominator).aggregate(
                Sum('answer'))['answer__sum']

    def answer_sum_for_interviewer(self, question, interviewer):
        return question.answer_class().objects.filter(interviewer=interviewer, question=question).\
            aggregate(Sum('answer'))['answer__sum']

    def compute_numerical_question_for_interviewer(self, interviewer):
        denominator = self.answer_sum_for_interviewer(self.denominator, interviewer)
        numerator = self.answer_sum_for_interviewer(self.numerator, interviewer)
        return self.process_formula(numerator, denominator, interviewer)

    def get_denominator_sum_based_on_question_type(self, interviewer, question):
        if question.is_multichoice():
            option_ids = []
            for option in self.denominator_options.all():
                option_ids.append(option.id)
            denominator_number = len(question.answer_class().objects.filter(interviewer=interviewer,
                                                                            answer__id__in=option_ids))
        else:
            denominator_number = self.answer_sum_for_interviewer(question, interviewer)
        return denominator_number

    def numerator_computation(self, interviewer, question):
        numerator_number = 1
        if question.is_multichoice():
            option_ids = []
            for option in self.numerator_options.all():
                option_ids.append(option.id)
            numerator_number = len(question.answer_class().objects.filter(interviewer=interviewer,
                                                                          answer__id__in=option_ids))
        else:
            numerator_number = self.answer_sum_for_interviewer(question, interviewer)
        return numerator_number

    def denominator_computation(self, interviewer, survey):
        denominator_number = 1

        if self.groups:
            all_members_in_group = []
            for household in survey.survey_household.all().filter(interviewer=interviewer):
                all_members_in_group.append(household.members_belonging_to_group(self.groups))

            denominator_number = len(all_members_in_group)
        elif self.count:
            denominator_number = self.get_denominator_sum_based_on_question_type(interviewer, self.count)

        elif self.denominator:
            denominator_number = self.get_denominator_sum_based_on_question_type(interviewer, self.denominator)

        return denominator_number

    def compute_for_household_with_sub_options(self, survey, interviewer):
        numerator_number = self.numerator_computation(interviewer, self.numerator)
        denominator_number = self.denominator_computation(interviewer, survey)
        return numerator_number/denominator_number

    def save_denominator_options(self, question_options):
        for option in question_options:
            self.denominator_options.add(option)

    def save_numerator_options(self, question_options):
        for option in question_options:
            self.numerator_options.add(option)