from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rapidsms.contrib.locations.models import Location


class LocationAutoComplete(models.Model):
    location = models.ForeignKey(Location, null=True)
    text = models.CharField(max_length=500)

    class Meta:
        app_label = 'survey'


def generate_auto_complete_text_for_location(location):
    auto_complete = LocationAutoComplete.objects.filter(location=location)
    if not auto_complete:
        auto_complete = LocationAutoComplete(location=location)
    else:
        auto_complete = auto_complete[0]
    parents = [location.name]
    while location.tree_parent:
        location = location.tree_parent
        parents.append(location.name)
    parents.reverse()
    auto_complete.text = " > ".join(parents)
    auto_complete.save()


@receiver(post_save, sender=Location)
def create_location_auto_complete_text(sender, instance, **kwargs):
    generate_auto_complete_text_for_location(instance)
    for location in instance.get_descendants():
        generate_auto_complete_text_for_location(location)


def auto_complete_text(self):
    return LocationAutoComplete.objects.get(location=self).text


Location.auto_complete_text = auto_complete_text