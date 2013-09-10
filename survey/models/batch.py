from django.db import models
from django.db.models import Max
from rapidsms.contrib.locations.models import Location
from survey.models.base import BaseModel


class Batch(BaseModel):
    order = models.PositiveIntegerField(max_length=2, null=True)
    name = models.CharField(max_length=100, blank=False,null=True)
    description = models.CharField(max_length=300,blank=True,null=True)

    def save(self, *args, **kwargs):
        last_order = Batch.objects.aggregate(Max('order'))['order__max']
        self.order = last_order + 1 if last_order else 1
        super(Batch, self).save(*args, **kwargs)

    class Meta:
        app_label = 'survey'


    @classmethod
    def currently_open_for(self, location):
        locations = location.get_ancestors(include_self=True)
        open_batches = BatchLocationStatus.objects.filter(location__in=locations)
        if open_batches.count() > 0:
            return open_batches.order_by('created').all()[:1].get().batch

    def first_question(self):
        return self.questions.get(order=1)

    def all_questions(self):
        return self.questions.all()

    def open_for_location(self, location):
        all_related_locations = location.get_descendants(include_self=False).all()
        for related_location in all_related_locations:
            self.open_locations.get_or_create(batch=self, location=related_location)

        return self.open_locations.get_or_create(batch=self, location=location)

    def is_closed_for(self, location):
        return self.open_locations.filter(location=location).count() == 0

    def is_open_for(self, location):
        return not self.is_closed_for(location)

    def close_for_location(self, location):
        self.open_locations.filter(batch=self).delete()

    def get_next_indicator(self, order, location):
        indicator = self.indicators.filter(order = order + 1)
        if indicator:
            return indicator[0]
        else:
            return self.get_indicator_from_next_open_batch(location = location)

    def get_next_open_batch(self, order, location):
        next_batch_in_order = Batch.objects.filter(order__gt = order).order_by('order')

        next_open_batch = location.open_batches.filter(batch__in = next_batch_in_order)
        if next_open_batch:
            return next_open_batch[0].batch

    def generate_report(self, investigator_klass):
        data = []
        header = ['Location', 'Household Head Name']
        questions = []
        for question in self.questions.order_by('order').filter(subquestion=False):
            questions.append(question)
            header.append(question.identifier)
            if question.is_multichoice():
                header.append('')
        data = [header]
        investigator_klass.get_summarised_answers_for(self, questions, data)
        return data

    def get_next_question(self, order, location):
        if self.is_open_for(location=location):
            question = self.questions.filter(order=order + 1)

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


class BatchLocationStatus(BaseModel):
    batch = models.ForeignKey(Batch, null=True, related_name="open_locations")
    location = models.ForeignKey(Location, null=True, related_name="open_batches")

    class Meta:
        app_label = 'survey'