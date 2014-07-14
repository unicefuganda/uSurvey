from django.db import models
from django.db.models import Max
from rapidsms.contrib.locations.models import Location
from survey.models.surveys import Survey
from survey.models.base import BaseModel
from survey.views.views_helper import get_descendants


class Batch(BaseModel):
    order = models.PositiveIntegerField(max_length=2, null=True)
    name = models.CharField(max_length=100, blank=False, null=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    survey = models.ForeignKey(Survey, null=True, related_name="batch")

    BATCH_IS_OPEN_MESSAGE = "Batch cannot be deleted because it is open in %s."
    BATCH_HAS_ANSWERS_MESSAGE = "Batch cannot be deleted because it has responses."

    def save(self, *args, **kwargs):
        last_order = Batch.objects.aggregate(Max('order'))['order__max']
        self.order = last_order + 1 if last_order else 1
        super(Batch, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        app_label = 'survey'
        unique_together = ('survey', 'name',)

    def other_surveys_with_open_batches_in(self, location):
        batch_ids = location.open_batches.all().exclude(batch__survey=self.survey).values_list('batch',flat=True)
        return Survey.objects.filter(batch__id__in = batch_ids)

    @classmethod
    def currently_open_for(self, location):
        locations = location.get_ancestors(include_self=True)
        open_batches = BatchLocationStatus.objects.filter(location__in=locations)
        if open_batches.count() > 0:
            return open_batches.order_by('created').all()[:1].get().batch

    def get_groups(self):
        questions = self.all_questions()
        return list(set(map(lambda question: question.group, questions)))

    def has_unanswered_question(self, member):
        for question in self.all_questions():
            if member.belongs_to(question.group) and not member.has_answered(question, self):
                return True
        return False

    def all_questions(self):
        from survey.models import BatchQuestionOrder
        return BatchQuestionOrder.get_batch_order_specific_questions(self, {})

    def open_for_location(self, location):
        all_related_locations = get_descendants(location, include_self=False)
        for related_location in all_related_locations:
            self.open_locations.get_or_create(batch=self, location=related_location)
        return self.open_locations.get_or_create(batch=self, location=location)

    def activate_non_response_for(self, location, status=True):
        all_related_locations = location.get_descendants(include_self=True).all()
        for related_location in all_related_locations:
            batch_location_status = self.open_locations.get(location=related_location)
            batch_location_status.non_response = status
            batch_location_status.save()

    def deactivate_non_response_for(self, location):
        self.activate_non_response_for(location, False)

    def non_response_is_activated_for(self, location):
        return self.open_locations.filter(location=location, non_response=True).count() > 0

    def is_closed_for(self, location):
        return self.open_locations.filter(location=location).count() == 0

    def is_open_for(self, location):
        return not self.is_closed_for(location)

    def get_non_response_active_locations(self):
        non_response_active_batch_location_status = self.open_locations.filter(non_response=True)
        locations = []
        map(lambda batch_status: locations.append(batch_status.location), non_response_active_batch_location_status)
        return locations

    def close_for_location(self, location):
        self.open_locations.filter(batch=self).delete()

    def get_next_open_batch(self, order, location):
        next_batch_in_order = Batch.objects.filter(order__gt = order).order_by('order')

        next_open_batch = location.open_batches.filter(batch__in = next_batch_in_order)
        if next_open_batch:
            return next_open_batch[0].batch

    def get_next_question(self, order, location):
        if self.is_open_for(location=location):
            question = self.questions.filter(order=order+1)

            if question:
                return question[0]
            else:
                return self.get_question_from_next_batch(location=location)
        else:
            return self.get_question_from_next_batch(location=location)

    def get_question_from_next_batch(self, location):
        next_batch = self.get_next_open_batch(order=self.order, location=location)
        if next_batch:
            return next_batch.get_next_question(order=0, location=location)

    def is_open(self):
        return self.open_locations.all().exists()

    def can_be_deleted(self):
        if self.is_open():
            the_country = Location.objects.get(tree_parent=None)
            open_in_locations_ids = self.open_locations.filter(location__tree_parent=the_country).values_list('location', flat=True)
            open_location_names = Location.objects.filter(id__in=open_in_locations_ids).values_list('name', 'type')
            return False, self.message_for_inability_to_delete(open_location_names)

        for question in self.all_questions():
            answer = question.answer_class().objects.filter(batch=self)
            if answer:
                return False, self.message_for_inability_to_delete()
        return True, ''

    def message_for_inability_to_delete(self, open_location_names=None):
        if open_location_names:
            return self.BATCH_IS_OPEN_MESSAGE % ", ".join([" ".join(item) for item in open_location_names])
        return self.BATCH_HAS_ANSWERS_MESSAGE

    @classmethod
    def open_ordered_batches(cls, location):
        all_batches = Batch.objects.all().order_by('order')
        open_batches = []
        for batch in all_batches:
            if batch.is_open_for(location):
                open_batches.append(batch)
        return open_batches


class BatchLocationStatus(BaseModel):
    batch = models.ForeignKey(Batch, null=True, related_name="open_locations")
    location = models.ForeignKey(Location, null=True, related_name="open_batches")
    non_response = models.BooleanField(null=False, default=False)