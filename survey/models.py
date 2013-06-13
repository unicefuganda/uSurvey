from django.db import models
from django_extensions.db.models import TimeStampedModel
from rapidsms.contrib.locations.models import Location
from django.db.models.signals import post_save
from django.dispatch import receiver
from investigator_configs import *

class Investigator(TimeStampedModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    mobile_number = models.CharField(max_length=20, unique=True, null=False, blank=False)
    male = models.BooleanField(default=True)
    age = models.PositiveIntegerField(max_length=2, null=True)
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION)
    location = models.ForeignKey(Location, null=True)
    language = models.CharField(max_length=100, null=True, choices=LANGUAGES)


    class Meta:
        app_label = 'survey'

class LocationAutoComplete(models.Model):
    location = models.ForeignKey(Location, null=True)
    text = models.CharField(max_length=500)

    class Meta:
        app_label = 'survey'

class Survey(TimeStampedModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=255, blank=False, null=False)

    class Meta:
        app_label = 'survey'

class Batch(TimeStampedModel):
    survey = models.ForeignKey(Survey, null=True, related_name="batches")

    class Meta:
        app_label = 'survey'

class Indicator(TimeStampedModel):
    batch = models.ForeignKey(Batch, null=True, related_name="indicators")
    order = models.PositiveIntegerField(max_length=2, null=True)

    class Meta:
        app_label = 'survey'

class Question(TimeStampedModel):
    NUMBER = 'number'
    TEXT = 'text'
    MULTICHOICE = 'multichoice'
    TYPE_OF_ANSWERS = (
        (NUMBER, 'NumberAnswer'),
        (TEXT, 'TextAnswer'),
        (MULTICHOICE, 'MultichoiceAnswer')
    )

    indicator = models.ForeignKey(Indicator, null=True, related_name="questions")
    text = models.CharField(max_length=100, blank=False, null=False)
    answer_type = models.CharField(max_length=100, blank=False, null=False, choices=TYPE_OF_ANSWERS)
    order = models.PositiveIntegerField(max_length=2, null=True)

    class Meta:
        app_label = 'survey'

    def options_in_text(self):
        options = [option.to_text() for option in self.options.order_by('order').all()]
        return "\n".join(options)

class QuestionOption(TimeStampedModel):
    question = models.ForeignKey(Question, null=True, related_name="options")
    text = models.CharField(max_length=100, blank=False, null=False)
    order = models.PositiveIntegerField(max_length=2, null=True)

    class Meta:
        app_label = 'survey'

    def to_text(self):
        return "%d) %s" % (self.order, self.text)

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
    auto_complete.text = ", ".join(parents)
    auto_complete.save()

@receiver(post_save, sender=Location)
def create_location_auto_complete_text(sender, instance, **kwargs):
    generate_auto_complete_text_for_location(instance)
    for location in instance.get_descendants():
        generate_auto_complete_text_for_location(location)

def auto_complete_text(self):
    return LocationAutoComplete.objects.get(location=self).text

Location.auto_complete_text = auto_complete_text