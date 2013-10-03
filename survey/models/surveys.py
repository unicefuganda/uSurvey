from django.db import models

from survey.models.base import BaseModel

class Survey(BaseModel):
    name = models.CharField(max_length=100, blank=False,null=True)
    description = models.CharField(max_length=300,blank=True,null=True)
    sample_size = models.PositiveIntegerField(max_length=2, null=False, blank=False, default=10, verbose_name="Number of Households per Investigator")
    type = models.BooleanField(default=False)

    class Meta:
        app_label = 'survey'

    def is_open(self):
        all_batches = self.batch.all()
        for batch in all_batches:
            if batch.open_locations.all():
                return True
        return False
