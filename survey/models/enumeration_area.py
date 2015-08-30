# from rapidsms.contrib.locations.models import Location
from survey.models.locations import Location
from survey.models import BaseModel
from django.db import models
from survey.models.surveys import Survey
from survey.models.batch import Batch, BatchLocationStatus

class EnumerationArea(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=True)
    total_households = models.PositiveIntegerField(null=True, blank=True)
    locations = models.ManyToManyField(Location, null=True, related_name="enumeration_areas")

    def __unicode__(self):
        return self.name

    def get_survey_openings(self, survey=None):
        parent_locations = set()
        ea_locations = self.locations.all()
        if ea_locations:
            map(lambda loc: parent_locations.update(loc.get_ancestors(include_self=True)), ea_locations)
        kwargs = {'location__pk__in' : [loc.pk for loc in parent_locations]}
        if survey:
            kwargs['batch__survey'] = survey
        location_registry =  BatchLocationStatus.objects.filter(**kwargs)
        return location_registry

    def open_surveys(self):
        location_registry = self.get_survey_openings()
        return list(Survey.objects.filter(pk__in=[reg.batch.survey.pk for reg in location_registry]))
    
    def open_batches(self, survey, house_member=None):
        location_registry = self.get_survey_openings(survey)
        batches = list([reg.batch for reg in location_registry])
        if house_member is not None:
            applicable = []
            for batch in batches:
                if batch.is_applicable(house_member):
                   applicable.append(batch)
            batches = applicable
        return sorted(batches, key=lambda batch: batch.order)

        
#     def validate_unique(self, *args, **kwargs):
#         super(EnumerationArea, self).validate_unique(*args, **kwargs)
#         