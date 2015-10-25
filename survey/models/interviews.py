import os
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from survey.models.access_channels import InterviewerAccess, ODKAccess, USSDAccess
from survey.models.base import BaseModel
from dateutil.parser import parse as extract_date
from rapidsms.contrib.locations.models import Point
from django import template
from survey.interviewer_configs import MESSAGES
from survey.utils.decorators import static_var
from django.db.models.signals import post_save
from django.dispatch import receiver

def reply_test(cls, func):
    func.is_reply_test = True
    return func

class Interview(BaseModel):
    interviewer = models.ForeignKey("Interviewer", null=True, related_name="interviews")
    householdmember = models.ForeignKey("HouseholdMember", null=True, related_name="interviews")
    batch = models.ForeignKey("Batch", related_name='interviews')
    interview_channel = models.ForeignKey(InterviewerAccess, related_name='interviews')
    closure_date = models.DateTimeField(null=True, blank=True, editable=False)
    last_question = models.ForeignKey("Question", related_name='ongoing', null=True, blank=True)

    def start(self):
        return self.batch.start_question

    def is_closed(self):
        return self.closure_date is not None

    def respond(self, reply=None, channel=ODKAccess.choice_name()):
        if self.is_closed():
            return
        # import pdb; pdb.set_trace()
        #get last question
        next_question = None
        try:
            if self.last_question is None:
                next_question = self.batch.start_question
            else:
                if reply is None: #if we are not replying, simply return last question or first question
                    next_question = self.last_question
                else:
                    print 'last question is ', self.last_question
                    answer_class = Answer.get_class(self.last_question.answer_type)
                    answer_class.create(self, self.last_question, reply)
                    #after answering the question, lets see if it leads us anywhere
                    next_question = self.last_question.next_question(reply)

                 #confirm if next question is applicable
                if next_question and (self.householdmember.belongs_to(next_question.group) and  \
                                    AnswerAccessDefinition.is_valid(channel, next_question.answer_type)) is False:
                    next_question = self.batch.next_inline(self.last_question, groups=self.householdmember.groups, channel=channel) #if not get next line question
        except Exception, ex:
            print 'error %s occurred', str(ex)
            next_question = self.last_question
            print 'but first last quest', self.last_question, ' next one: ', next_question
        if next_question:
            self.last_question = next_question
            print 'last question now is ', next_question
            self.save()
            response_text = self.householdmember.get_composed(next_question.display_text(USSDAccess.choice_name()))
            print 'response text is: ', response_text
            return response_text
        # #if there is nothing left to ask, just close this survey
        # self.closure_date = datetime.now()
        # self.save()
        print 'nothing here mehn', next_question

    # @property
    # def has_pending_questions(self):
    #     return self.last_question is not None and self.last_question.flows.filter(next_question__isnull=False).exists()

    @classmethod
    def pending_batches(cls, house_member, ea, survey):
        available_batches = ea.open_batches(survey)
        print 'available batches: ', available_batches
        completed_interviews = Interview.objects.filter(householdmember=house_member, batch__in=available_batches,
                                                        closure_date__isnull=False)
        completed_batches = [interview.batch for interview in completed_interviews]
        return [batch for batch in available_batches if batch.start_question and batch not in completed_batches]

    @classmethod
    def interviews(cls, house_member, interviewer, survey):
        available_batches = interviewer.ea.open_batches(survey, house_member)
        interviews = Interview.objects.filter(householdmember=house_member, batch__in=available_batches)
        #return (completed_interviews, pending_interviews)
        return (interviews.filter(closure_date__isnull=False), interviews.filter(closure_date__isnull=True))
#         completed_batches = [interview.batch for interview in completed_interviews]
#         return [batch for batch in available_batches if batch not in completed_batches]


    def members_with_open_batches(self):
        pass


#     @property
#     def first_question(self):
#         question = self.batch.start_question

    class Meta:
        app_label = 'survey'
        unique_together = [('householdmember', 'batch'), ]


class Answer(BaseModel):
    interview = models.ForeignKey(Interview, related_name='%(class)s')
#     interviewer_response = models.CharField(max_length=200)  #This shall hold the actual response from interviewer
#                                                             #value shall hold the exact worth of the response
    question = models.ForeignKey("Question", null=True, related_name="%(class)s", on_delete=models.PROTECT)

    @classmethod
    def create(cls, interview, question, answer):
        return cls.objects.create(question=question, value=answer, interview=interview)

    @classmethod
    def supported_answers(cls):
        return Answer.__subclasses__()

    @classmethod
    def answer_types(cls):
        return [cl.choice_name() for cl in Answer.__subclasses__() if cl is not NonResponseAnswer]

    @classmethod
    def get_class(cls, verbose_name):
        verbose_name = verbose_name.strip()
        for cl in Answer.__subclasses__():
            if cl._meta.verbose_name.title() == verbose_name:
                return cl
        ValueError('unknown class')

    def to_text(self):
        return self.value

    @classmethod
    def choice_name(cls):
        return cls._meta.verbose_name.title()

    @classmethod
    def contains(cls, answer, txt):
        answer = answer.lower()
        txt = txt.lower()
        try:
            return answer.index(txt) >= 0
        except ValueError:
            return False

    @classmethod
    def odk_contains(cls, node_path, value):
        return "regex(%s, '.*(%s).*')" % (node_path, value)

    @classmethod
    def equals(cls, answer, value):
        return answer == value

    @classmethod
    def odk_equals(cls, node_path, value):
        return "%s = '%s'" % (node_path, value)

    @classmethod
    def starts_with(cls, answer, txt):
        answer = answer.lower()
        txt = txt.lower()
        return answer.startswith(txt)

    @classmethod
    def odk_starts_with(cls, node_path, value):
        return "regex(%s, '^(%s).*')" % (node_path, value)

    @classmethod
    def ends_with(cls, answer, txt):
        answer = answer.lower()
        txt = txt.lower()
        return answer.endswith(txt)

    @classmethod
    def odk_ends_with(cls, node_path, value):
        return "regex(%s, '.*(%s)$')" % (node_path, value)

    @classmethod
    def greater_than(cls, answer, value):
        return answer > value

    @classmethod
    def odk_greater_than(cls, node_path, value):
        return "%s &gt; '%s'" % (node_path, value)

    @classmethod
    def less_than(cls, answer, value):
        return answer < value

    @classmethod
    def odk_less_than(cls, node_path, value):
        return "%s &lt; '%s'" % (node_path, value)

    @classmethod
    def between(cls, answer, lowerlmt, upperlmt):
        return upperlmt > answer >= lowerlmt

    @classmethod
    def odk_between(cls, node_path, lowerlmt, upperlmt):
        return "(%s &gt; '%s') and (%s &lt; '%s')" % (node_path, lowerlmt, node_path, upperlmt)

    @classmethod
    def print_odk_validation(cls, node_path, validator_name, *args):
        printer = getattr(cls, 'odk_%s'%validator_name)
        return printer(node_path, *args)

    @classmethod
    def passes_test(cls, text_exp):
        return bool(eval(text_exp))

    @classmethod
    def validators(cls):
        return [cls.starts_with, cls.ends_with, cls.equals, cls.between, cls.less_than,
                cls.greater_than, cls.contains, ]

    class Meta:
        app_label = 'survey'
        abstract = True
        get_latest_by = 'created'

class NumericalAnswer(Answer):
    value = models.PositiveIntegerField(max_length=5, null=True)

    @classmethod
    def validators(cls):
        return [cls.greater_than, cls.equals, cls.less_than, cls.between]

    @classmethod
    def create(cls, interview, question, answer):
        try:
            value = int(answer)
        except Exception: raise
        return cls.objects.create(question=question, value=answer, interview=interview)

    @classmethod
    def greater_than(cls, answer, value):
        answer = int(answer)
        value = int(value)
        return answer > value

    @classmethod
    def odk_greater_than(cls, node_path, value):
        return "%s &gt; %s" % (node_path, value)

    @classmethod
    def less_than(cls, answer, value):
        answer = int(answer)
        value = int(value)
        return answer < value

    @classmethod
    def odk_less_than(cls, node_path, value):
        return "%s &lt; %s" % (node_path, value)

    @classmethod
    def between(cls, answer, lowerlmt, upperlmt):
        answer = int(answer)
        upperlmt = int(upperlmt)
        lowerlmt = int(lowerlmt)
        return upperlmt > answer >= lowerlmt

    @classmethod
    def odk_between(cls, node_path, lowerlmt, upperlmt):
        return "(%s &gt; %s) and (%s &lt; %s)" % (node_path, lowerlmt, node_path, upperlmt)


    class Meta:
        app_label = 'survey'
        abstract = False

class ODKGeoPoint(Point):
    altitude = models.DecimalField(decimal_places=3, max_digits=10)
    precision = models.DecimalField(decimal_places=3, max_digits=10)

    class Meta:
        app_label = 'survey'
        abstract = False

class TextAnswer(Answer):
    value = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.starts_with, cls.equals, cls.ends_with, cls.contains]

    @classmethod
    def equals(cls, answer, value):
        answer = answer.lower()
        value = value.lower()
        return answer == value

class MultiChoiceAnswer(Answer):
    value = models.ForeignKey("QuestionOption", null=True)

    @classmethod
    def create(cls, interview, question, answer):
        try:
            answer = int(answer)
            answer = question.options.get(order=answer)
        except:
            pass
        return cls.objects.create(question=question, value=answer, interview=interview)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.equals, ]

    def to_text(self):
        return self.value.text


    @classmethod
    @static_var('label', 'Equals Option')
    def equals(cls, answer, txt):
        return super(MultiChoiceAnswer, cls).equals(answer, txt)

class MultiSelectAnswer(Answer):
    value = models.ManyToManyField("QuestionOption", null=True)

    @classmethod
    def create(cls, interview, question, answer):
        if isinstance(answer, basestring):
            answer = answer.split(' ')
        if isinstance(answer, list):
            selected = [a.lower() for a in answer]
            options = question.options.all()
            chosen = [op.pk for op in options if op.text.lower() in selected]
            selected = question.options.filter(pk__in=chosen)
        else:
            selected = answer
        ans = cls.objects.create(question=question, interview=interview)
        for opt in selected:
            ans.value.add(opt)
        return ans

    # def __init__(self, question, answer, *args, **kwargs):
    #     super(MultiSelectAnswer, self).__init__(*args, **kwargs)
    #     if isinstance(answer, basestring):
    #         answer = answer.split(' ')
    #     if isinstance(answer, list):
    #         selected = [a.lower() for a in answer]
    #         options = question.options.all()
    #         chosen = [op.pk for op in options if op.text.lower() in selected]
    #         self.selected = question.options.filter(pk__in=chosen)
    #     else:
    #         self.selected = answer
    #     self.question = question

    class Meta:
        app_label = 'survey'
        abstract = False

    def to_text(self):
        texts = []
        map(lambda opt: texts.append(opt.text), self.value.all())
        return ' and '.join(texts)

    @classmethod
    def validators(cls):
        return [cls.equals, cls.contains]

    @classmethod
    def equals(cls, answer, txt):
        return answer.text.lower() == txt.lower()

class DateAnswer(Answer):
    value = models.DateField(null=True)

    @classmethod
    def create(cls, interview, question, answer):
        if isinstance(answer, basestring):
            answer = extract_date(answer, fuzzy=True)
        question = question
        return cls.objects.create(question=question, value=answer, interview=interview)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.greater_than, cls.equals, cls.less_than, cls.between]

class AudioAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []

    def to_text(self):
        return ''


class VideoAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []

    def to_text(self):
        return ''

class ImageAnswer(Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []

    def to_text(self):
        return ''

class GeopointAnswer(Answer):
    value = models.ForeignKey(ODKGeoPoint, null=True)

    @classmethod
    def create(cls, interview, question, answer):
        if isinstance(answer, basestring):
            answer = answer.split(' ')
            answer = ODKGeoPoint(latitude=answer[0], longitude=answer[1], altitude=[2], precision=answer[3])
        return cls.objects.create(question=question, value=answer, interview=interview)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.equals]

    def to_text(self):
        return ''

class NonResponseAnswer(Answer):
    value = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []


class AnswerAccessDefinition(BaseModel):
    ACCESS_CHANNELS = [(name, name) for name in InterviewerAccess.access_channels()]
    ANSWER_TYPES = [(name, name) for name in Answer.answer_types()]
    answer_type = models.CharField(max_length=100, choices=ANSWER_TYPES)
    channel = models.CharField(max_length=100, choices=ACCESS_CHANNELS)

    class Meta:
        app_label = 'survey'
        unique_together = [('answer_type', 'channel'), ]

    @classmethod
    def is_valid(cls, channel, answer_type):
        try:
            return cls.objects.get(answer_type=answer_type, channel=channel) is not None
        except cls.DoesNotExist:
            return False

    @classmethod
    def answer_types(cls, channel):
        return set(AnswerAccessDefinition.objects.filter(channel=channel).values_list('answer_type', flat=True))
