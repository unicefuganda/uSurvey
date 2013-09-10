from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError

from survey.models.base import BaseModel
from survey.models.batch import Batch
from survey.models.investigator import Investigator
from survey.models.question import Question


class Formula(BaseModel):
    name = models.CharField(max_length=50,unique=True, blank=False)
    numerator = models.ForeignKey(Question, blank=False, related_name="as_numerator")
    denominator = models.ForeignKey(Question, blank=False, related_name="as_denominator")
    batch = models.ForeignKey(Batch, null=True, related_name="formula")

    class Meta:
        app_label = 'survey'


    def clean(self, *args, **kwargs):
        if self.numerator.batch != self.denominator.batch:
            raise ValidationError('Numerator and Denominator must belong to the same batch')

    def save(self, *args, **kwargs):
        self.clean(*args, **kwargs)
        super(Formula, self).save(*args, **kwargs)

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
        return sum(values)/len(values)

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
            values[ option.text ] = self.process_formula(numerator, denominator, investigator)
        return values

    def compute_numerator_for_option(self, option, investigator):
        households = self.numerator.answer_class().objects.filter(investigator=investigator, answer=option).values_list('household', flat=True)
        return self.denominator.answer_class().objects.filter(household__in=households, question=self.denominator).aggregate(Sum('answer'))['answer__sum']

    def answer_sum_for_investigator(self, question, investigator):
        return question.answer_class().objects.filter(investigator=investigator, question=question).aggregate(Sum('answer'))['answer__sum']

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
