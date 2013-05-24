from django.db import models
from django_extensions.db.models import TimeStampedModel
from rapidsms.contrib.locations.models import Location
from django.db.models.signals import post_save
from django.dispatch import receiver

class Investigator(TimeStampedModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    mobile_number = models.CharField(max_length=20, unique=True, null=False, blank=False)
    male = models.BooleanField(default=True)
    age = models.PositiveIntegerField(max_length=2, null=True)
    level_of_education = models.CharField(max_length=100, null=True)
    location = models.ForeignKey(Location, null=True)


    class Meta:
        app_label = 'survey'

class LocationAutoComplete(models.Model):
    location = models.ForeignKey(Location, null=True)
    text = models.CharField(max_length=500)

@receiver(post_save, sender=Location)
def create_location_auto_complete_text(sender, instance, **kwargs):
    auto_complete = LocationAutoComplete.objects.filter(location=instance)

    if not auto_complete:
        auto_complete = LocationAutoComplete(location=instance)
    else:
        auto_complete = auto_complete[0]

    parents = [instance.name]

    while instance.tree_parent:
        instance = instance.tree_parent
        parents.append(instance.name)

    auto_complete.text = ", ".join(parents)
    auto_complete.save()

def auto_complete_text(self):
    return LocationAutoComplete.objects.get(location=self).text

Location.auto_complete_text = auto_complete_text