from django.db import models
from django_extensions.db.models import TimeStampedModel
from rapidsms.contrib.locations.models import Location
from django.db.models.signals import post_save
from django.dispatch import receiver
from investigator_configs import *

class BaseModel(TimeStampedModel):
    class Meta:
        app_label = 'survey'
        abstract = True

class Investigator(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    mobile_number = models.CharField(max_length=20, unique=True, null=False, blank=False)
    male = models.BooleanField(default=True)
    age = models.PositiveIntegerField(max_length=2, null=True)
    level_of_education = models.CharField(max_length=100, null=True, choices=LEVEL_OF_EDUCATION)
    location = models.ForeignKey(Location, null=True)
    language = models.CharField(max_length=100, null=True, choices=LANGUAGES)

    def next_answerable_question(self):
        last_answered_question = self.last_answered_question()
        if not last_answered_question:
            return Survey.currently_open().first_question()
        else:
            return last_answered_question.next_question()

    def last_answered_question(self):
        answered = []
        for klass in [NumericalAnswer, TextAnswer, MultiChoiceAnswer]:
            try:
                answer = klass.objects.filter(investigator=self).latest()
                if answer: answered.append(answer)
            except klass.DoesNotExist, e:
                pass
        if answered:
            return sorted(answered, key=lambda x: x.created, reverse=True)[0].question

    def answered(self, question, household, answer):
        answer_class = eval(Question.TYPE_OF_ANSWERS_CLASS[question.answer_type])
        if answer_class == MultiChoiceAnswer:
            answer = question.options.get(order=int(answer))
        answer_class.objects.create(investigator=self, question=question, household=household, answer=answer)
        return question.next_question()

class LocationAutoComplete(models.Model):
    location = models.ForeignKey(Location, null=True)
    text = models.CharField(max_length=500)

    class Meta:
        app_label = 'survey'

class Survey(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=255, blank=False, null=False)

    def first_question(self):
        return self.batches.reverse().latest('created').indicators.reverse().latest('order').questions.reverse().latest('order')

    @classmethod
    def currently_open(self):
        return Survey.objects.latest('created')

class Batch(BaseModel):
    survey = models.ForeignKey(Survey, null=True, related_name="batches")

class Indicator(BaseModel):
    batch = models.ForeignKey(Batch, null=True, related_name="indicators")
    order = models.PositiveIntegerField(max_length=2, null=True)

class Question(BaseModel):
    NUMBER = 'number'
    TEXT = 'text'
    MULTICHOICE = 'multichoice'
    TYPE_OF_ANSWERS = {
        (NUMBER, 'Number'),
        (TEXT, 'Text'),
        (MULTICHOICE, 'Multichoice')
    }
    TYPE_OF_ANSWERS_CLASS = {
        NUMBER: 'NumericalAnswer',
        TEXT: 'TextAnswer',
        MULTICHOICE: 'MultiChoiceAnswer'
    }

    indicator = models.ForeignKey(Indicator, null=True, related_name="questions")
    text = models.CharField(max_length=100, blank=False, null=False)
    answer_type = models.CharField(max_length=100, blank=False, null=False, choices=TYPE_OF_ANSWERS)
    order = models.PositiveIntegerField(max_length=2, null=True)

    def options_in_text(self):
        options = [option.to_text() for option in self.options.order_by('order').all()]
        return "\n".join(options)

    def next_question(self):
        question = self.indicator.questions.filter(order__gt=self.order)
        if question:
            return question[0]

    def to_ussd(self):
        return self.text

class QuestionOption(BaseModel):
    question = models.ForeignKey(Question, null=True, related_name="options")
    text = models.CharField(max_length=100, blank=False, null=False)
    order = models.PositiveIntegerField(max_length=2, null=True)

    def to_text(self):
        return "%d) %s" % (self.order, self.text)

class HouseHold(BaseModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    investigator = models.ForeignKey(Investigator, null=True, related_name="households")

class Answer(BaseModel):
    investigator = models.ForeignKey(Investigator, null=True)
    household = models.ForeignKey(HouseHold, null=True)
    question = models.ForeignKey(Question, null=True)

    class Meta:
        app_label = 'survey'
        abstract = True
        get_latest_by = 'created'

class NumericalAnswer(Answer):
    answer = models.PositiveIntegerField(max_length=5, null=True)

    def save(self, *args, **kwargs):
        self.answer = int(self.answer)
        super(NumericalAnswer, self).save(*args, **kwargs)

class TextAnswer(Answer):
    answer = models.CharField(max_length=100, blank=False, null=False)

class MultiChoiceAnswer(Answer):
    answer = models.ForeignKey(QuestionOption, null=True)

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