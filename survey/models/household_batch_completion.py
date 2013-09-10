from django.db.models import Count
from rapidsms.contrib.locations.models import Location
from survey.investigator_configs import NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR
from survey.models.investigator import Investigator
from survey.models.base import BaseModel
from survey.models.batch import Batch
from django.db import models
from survey.models.households import Household



class HouseholdBatchCompletion(BaseModel):
    household = models.ForeignKey(Household, null=True, related_name="completed_batches")
    batch = models.ForeignKey(Batch, null=True, related_name="completed_households")
    investigator = models.ForeignKey(Investigator, null=True, related_name="completed_batches")

    @classmethod
    def households_status(self, investigators, batch):
        households = Household.objects.filter(investigator__in = investigators)
        completed = batch.completed_households.filter(household__in = households).count()
        pending = households.count() - completed
        return {'completed': completed, 'pending': pending}

    @classmethod
    def clusters_status(self, investigators, batch):
        completed_clusters = self.objects.values('investigator').annotate(number_of_households=Count('household')).filter(number_of_households = NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR, batch = batch, investigator__in = investigators).count()
        pending_clusters = investigators.count() - completed_clusters
        return {'completed': completed_clusters, 'pending': pending_clusters}

    @classmethod
    def pending_investigators(self, investigators, batch):
        completed_clusters = self.objects.values('investigator').annotate(number_of_households=Count('household')).filter(number_of_households = NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR, batch = batch)
        investigator_ids = completed_clusters.values_list('investigator', flat=True)
        return investigators.exclude(id__in=investigator_ids)


    @classmethod
    def status_of_batch(self, batch, location):
        locations = location.get_descendants(include_self=True) if location else Location.objects.all()
        investigators = Investigator.objects.filter(location__in = locations)
        return self.households_status(investigators, batch), self.clusters_status(investigators, batch), self.pending_investigators(investigators, batch)



