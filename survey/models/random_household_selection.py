import random
from django.db import models
from rapidsms.router import send
from survey.investigator_configs import NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR
from survey.models.backend import Backend
from survey.models.base import BaseModel
from survey.models.investigator import Investigator

class RandomHouseHoldSelection(BaseModel):
    mobile_number = models.CharField(max_length=10, unique=True, null=False, blank=False)
    no_of_households = models.PositiveIntegerField(null=True)
    selected_households = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        app_label = 'survey'


    def generate_new_list(self):
        selected_households = random.sample(list(range(1, self.no_of_households + 1)), NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR)
        selected_households.sort()
        self.selected_households = ",".join(str(x) for x in selected_households)
        self.save()

    def text_message(self):
        return "Dear investigator, these are the selected households: %s" % self.selected_households

    def generate(self, no_of_households):
        if not self.selected_households:
            self.no_of_households = no_of_households
            self.generate_new_list()
        investigator = Investigator(mobile_number=self.mobile_number)
        investigator.backend = Backend.objects.all()[0]
        send(self.text_message(), [investigator])