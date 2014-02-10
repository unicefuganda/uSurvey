import random
from django.db import models
from rapidsms.router import send
from survey.investigator_configs import NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR
from survey.models import Household, LocationCode
from survey.models.backend import Backend
from survey.models.base import BaseModel
from survey.models.investigator import Investigator


class RandomHouseHoldSelection(BaseModel):
    mobile_number = models.CharField(max_length=10, null=False, blank=False)
    no_of_households = models.PositiveIntegerField(null=True)
    selected_households = models.TextField(blank=False, null=False)
    survey = models.ForeignKey("Survey", null=True, related_name="random_household")

    class Meta:
        app_label = 'survey'

    def generate_new_list(self, survey):
        if survey.has_sampling:
            selected_households = random.sample(list(range(1, self.no_of_households + 1)), NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR)
            selected_households.sort()
        else:
            selected_households = range(1, self.no_of_households + 1)
        self.selected_households = ",".join(str(x) for x in selected_households)
        self.save()

    def text_message(self):
        return "Dear investigator, these are the selected households: %s" % self.selected_households

    def send_message(self):
        investigator = Investigator(mobile_number=self.mobile_number)
        investigator.backend = Backend.objects.all()[0]
        send(self.text_message(), [investigator])

    def generate(self, no_of_households, survey):
        if not self.selected_households:
            self.no_of_households = no_of_households
            self.generate_new_list(survey)

        all_selected_households = RandomHouseHoldSelection.objects.filter(mobile_number=self.mobile_number, survey=survey)[0].selected_households
        all_random_households = all_selected_households.split(',')

        investigator = Investigator.objects.get(mobile_number=self.mobile_number)

        for random_household in all_random_households:
            uid = Household.next_uid(survey)
            household_code_value = LocationCode.get_household_code(investigator) + str(uid)
            Household.objects.create(investigator=investigator, ea=investigator.ea,
                                     uid=uid, random_sample_number=random_household,
                                     survey=survey, household_code=household_code_value)

        if survey.has_sampling:
            self.send_message()