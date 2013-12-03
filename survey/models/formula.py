from django.db import models
from django.db.models import Sum

from survey.models.base import BaseModel
from survey.models.investigator import Investigator
from survey.models.question import Question, QuestionOption


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

    def compute_for_location(self, location):
        investigators = Investigator.lives_under_location(location)
        if self.numerator.is_multichoice():
            return self.compute_multichoice_question_for_investigators(investigators)
        else:
            return self.compute_numerical_question_for_investigators(investigators)

    def compute_for_next_location_type_in_the_hierarchy(self, current_location):
        locations = current_location.get_children()
        data = {}
        for location in locations:
            data[location] = self.compute_for_location(location)
        return data

    def compute_numerical_question_for_investigators(self, investigators):
        values = []
        for investigator in investigators:
            values.append(self.compute_numerical_question_for_investigator(investigator))
        return sum(values) / len(values)

    def compute_multichoice_question_for_investigators(self, investigators):
        values = []
        computed_dict = {}
        for investigator in investigators:
            values.append(self.compute_multichoice_question_for_investigator(investigator))

        denominator = len(values)
        for option in self.numerator.options.all():
            numerator = sum([value[option.text] for value in values])
            computed_dict[option.text] = numerator / denominator
        return computed_dict

    def process_formula(self, numerator, denominator, investigator):
        return ((numerator * investigator.weights) / denominator) * 100

    def compute_multichoice_question_for_investigator(self, investigator):
        values = {}
        denominator = self.answer_sum_for_investigator(self.denominator, investigator)
        for option in self.numerator.options.all():
            numerator = self.compute_numerator_for_option(option, investigator)
            values[option.text] = self.process_formula(numerator, denominator, investigator)
        return values

    def compute_numerator_for_option(self, option, investigator):
        households = self.numerator.answer_class().objects.filter(investigator=investigator, answer=option).values_list(
            'household', flat=True)
        return \
            self.denominator.answer_class().objects.filter(household__in=households,
                                                           question=self.denominator).aggregate(
                Sum('answer'))['answer__sum']

    def answer_sum_for_investigator(self, question, investigator):
        return question.answer_class().objects.filter(investigator=investigator, question=question).\
            aggregate(Sum('answer'))['answer__sum']

    def answer_for_household(self, question, household):
        return question.answer_class().objects.get(household=household, question=question).answer

    def compute_numerical_question_for_investigator(self, investigator):
        denominator = self.answer_sum_for_investigator(self.denominator, investigator)
        numerator = self.answer_sum_for_investigator(self.numerator, investigator)
        return self.process_formula(numerator, denominator, investigator)

    def weight_for_location(self, location):
        investigator = Investigator.objects.filter(location=location)
        if investigator:
            return investigator[0].weights

    def compute_for_households_in_location(self, location):
        investigator = Investigator.objects.filter(location=location)
        household_data = {}
        if investigator:
            for household in investigator[0].households.all():
                household_data[household] = {
                    self.numerator: self.answer_for_household(self.numerator, household),
                    self.denominator: self.answer_for_household(self.denominator, household),
                }
        return household_data

    def get_denominator_sum_based_on_question_type(self, investigator, question):
        if question.is_multichoice():
            option_ids = []
            for option in self.denominator_options.all():
                option_ids.append(option.id)

            denominator_number = len(question.answer_class().objects.filter(investigator=investigator,
                                                                            answer__id__in=option_ids))
        else:
            denominator_number = self.answer_sum_for_investigator(question, investigator)

        return denominator_number

    def numerator_computation(self, investigator, question):
        numerator_number = 1

        if question.is_multichoice():
            option_ids = []
            for option in self.numerator_options.all():
                option_ids.append(option.id)

            numerator_number = len(question.answer_class().objects.filter(investigator=investigator,
                                                                          answer__id__in=option_ids))
        else:
            numerator_number = self.answer_sum_for_investigator(question, investigator)

        return numerator_number

    def denominator_computation(self, investigator, survey):
        denominator_number = 1

        if self.groups:
            all_members_in_group = []
            for household in survey.survey_household.all().filter(investigator=investigator):
                all_members_in_group.append(household.members_belonging_to_group(self.groups))

            denominator_number = len(all_members_in_group)
        elif self.count:
            denominator_number = self.get_denominator_sum_based_on_question_type(investigator, self.count)

        elif self.denominator:
            denominator_number = self.get_denominator_sum_based_on_question_type(investigator, self.denominator)

        return denominator_number

    def compute_for_household_with_sub_options(self, survey, investigator):
        numerator_number = self.numerator_computation(investigator, self.numerator)
        denominator_number = self.denominator_computation(investigator, survey)
        return numerator_number/denominator_number

    def save_denominator_options(self, question_options):
        for option in question_options:
            self.denominator_options.add(option)

    def save_numerator_options(self, question_options):
        for option in question_options:
            self.numerator_options.add(option)