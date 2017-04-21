import string
from datetime import datetime
from django_rq import job
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil.parser import parse as extract_date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from survey.models.base import BaseModel
from survey.models.access_channels import InterviewerAccess, ODKAccess, USSDAccess
from survey.models.locations import Point
from survey.utils.decorators import static_var


@job('default')
def update_model_obj_serial(model_obj, serial_name, filter_criteria):
    # get last assigned serial for interview survey in the interviewe ea
    max_serial = model_obj.__class__.objects.filter(**filter_criteria
                                                    ).aggregate(Max(serial_name)).get('%s__max'%serial_name, 0)
    setattr(model_obj, serial_name, max_serial + 1)
    model_obj.save()


class Interview(BaseModel):
    interviewer = models.ForeignKey(
        "Interviewer", null=True, related_name="interviews")    # nullable for simulation & backend load
    ea = models.ForeignKey(
        'EnumerationArea', related_name='interviews', db_index=True, null=True)    # repeated here for easy reporting
    survey = models.ForeignKey('Survey', related_name='interviews', db_index=True, null=True)
    question_set = models.ForeignKey('QuestionSet', related_name='interviews', db_index=True)
    interview_reference = models.ForeignKey('Interview', related_name='follow_up_interviews', null=True, blank=True)
    interview_channel = models.ForeignKey(InterviewerAccess, related_name='interviews', null=True)
    closure_date = models.DateTimeField(null=True, blank=True, editable=False)
    uploaded_by = models.ForeignKey(User, null=True, blank=True)     # just used to capture preview/data entry tester
    test_data = models.BooleanField(default=False)
    #instance_id = models.CharField(max_length=200, null=True, blank=True)
    last_question = models.ForeignKey(
        "Question", related_name='ongoing', null=True, blank=True)

    def __unicode__(self):
        return '%s: %s' % (self.id, self.batch.name)

    def is_closed(self):
        return self.closure_date is not None

    @property
    def qset(self):
        from survey.models.questions import QuestionSet
        return QuestionSet.get(pk=self.question_set.pk)

    @property
    def has_started(self):
        return self.last_question is not None

    def get_answer(self, question, capwords=True):
        answers = Answer.objects.filter(interview=self, question=question)
        if answers.exists():
            reply = unicode(answers[0].to_text())
            if capwords:
                reply = string.capwords(reply)
            return reply
        return ''

    @classmethod
    def save_answers(cls, qset, survey, ea, access_channel, question_map, answers, survey_parameters=None,
                     reference_interview=None, media_files=None):
        """Used to save a dictionary list of answers. keys in each answer dict must be keys in the question map
        :param qset:
        :param survey:
        :param ea:
        :param access_channel:
        :param question_map:
        :param answers:
        :param survey_parameters:
        :param reference_interview:
        :param media_files:
        :return:
        """
        interviewer = access_channel.interviewer
        interviews = []

        def _save_record(record):
            interview = Interview.objects.create(survey=survey, question_set=qset,
                                                 ea=ea, interviewer=interviewer, interview_channel=access_channel,
                                                 closure_date=timezone.now(),
                                                 interview_reference_id=reference_interview)
            interviews.append(interview)
            map(lambda (q_id, answer): _save_answer(interview, q_id, answer), record.items())
            if survey_parameters:
                map(lambda (q_id, answer): _save_answer(interview, q_id, answer), survey_parameters.items())

        def _save_answer(interview, q_id, answer):
            question = question_map.get(q_id, None)
            if question and answer:
                answer_class = Answer.get_class(question.answer_type)
                if question.answer_type in [AudioAnswer.choice_name(), ImageAnswer.choice_name(),
                                            VideoAnswer.choice_name()]:
                    answer = media_files.get(answer, None)
                try:
                    old_answer = answer_class.objects.get(interview=interview, question=question)
                    old_answer.update(answer)
                except answer_class.DoesNotExist:
                    answer_class.create(interview, question, answer)
                except Exception, ex:
                    print 'exception: %s' % str(ex)
        map(_save_record, answers)
        return interviews

    def respond(self, reply=None, channel=ODKAccess.choice_name()):
        """
            Respond to given reply for specified channel.
            This method is volatile.Raises exception if some error happens in the process
        :param reply:
        :param channel:
        :return: Returns next question if any
        """
        if self.is_closed():
            return
        if self.last_question and reply is None:
            return self.householdmember.get_composed(self.last_question.display_text(USSDAccess.choice_name()))
        next_question = None
        if self.has_started:
            # save reply
            answer_class = Answer.get_class(self.last_question.answer_type)
            answer_class.create(self, self.last_question, reply)
            # compute nnext
            next_question = self.last_question.next_question(reply)
        else:
            next_question = self.batch.start_question
        # now confirm the question is applicable
        if next_question and (self.householdmember.belongs_to(next_question.group)
                              and AnswerAccessDefinition.is_valid(channel, next_question.answer_type)) is False:
            next_question = self.batch.next_inline(self.last_question, groups=self.householdmember.groups,
                                                   channel=channel)  # if not get next line question
        response_text = None
        if next_question:
            self.last_question = next_question
            response_text = self.householdmember.get_composed(
                next_question.display_text(USSDAccess.choice_name()))
        else:
            print 'interview batch ', self.batch.name
            # if self.batch.name == 'Test5':
            #     import pdb; pdb.set_trace()
            # no more questions to ask. capture this time as closure
            self.closure_date = datetime.now()
        self.save()
        return response_text

    # @property
    # def has_pending_questions(self):
    # return self.last_question is not None and
    # self.last_question.flows.filter(next_question__isnull=False).exists()

    @classmethod
    def pending_batches(cls, house_member, ea, survey, available_batches):
        if available_batches is None:
            available_batches = ea.open_batches(survey)
        print 'available batches: ', available_batches
        completed_interviews = Interview.objects.filter(householdmember=house_member, batch__in=available_batches,
                                                        closure_date__isnull=False)
        completed_batches = [
            interview.batch for interview in completed_interviews]
        return [batch for batch in available_batches if batch.start_question and batch not in completed_batches]

    @classmethod
    def interviews(cls, house_member, interviewer, survey):
        available_batches = interviewer.ea.open_batches(survey, house_member)
        interviews = Interview.objects.filter(
            householdmember=house_member, batch__in=available_batches)
        # return (completed_interviews, pending_interviews)
        return (interviews.filter(closure_date__isnull=False), interviews.filter(closure_date__isnull=True))
#         completed_batches = [interview.batch for interview in completed_interviews]
# return [batch for batch in available_batches if batch not in
# completed_batches]

    def members_with_open_batches(self):
        pass

    @classmethod
    def interviews_in(cls, location, survey=None):
        kwargs = {'ea__locations__in': location.get_leafnodes(True)}
        if survey:
            kwargs['survey'] = survey
        return Interview.objects.filter(**kwargs)

    @classmethod
    def interviews(cls, survey):
        return Interview.objects.filter(survey=survey)

    class Meta:
        app_label = 'survey'


class Answer(BaseModel):
    # now question_type is used to store the exact question we are answering (Listing, Batch, personal info)
    question_type = models.CharField(max_length=100)  # I think using generic models is an overkill since they're all
    # questions
    interview = models.ForeignKey(Interview, related_name='%(class)s', db_index=True)
    question = models.ForeignKey("Question", null=True, related_name="%(class)s",
                                 on_delete=models.PROTECT, db_index=True)
    identifier = models.CharField(max_length=200, db_index=True)    # basically calculated field for reporting
    as_text = models.CharField(max_length=200, db_index=True)      # basically calculated field for reporting
    as_value = models.CharField(max_length=200, db_index=True)     # basically calculated field for reporting

    @classmethod
    def create(cls, interview, question, answer, as_text=None, as_value=None):
        try: # check if text and value is convertable to strings
            if as_text is None:
                as_text = str(answer)[:200]
            if as_value is None:
                as_value = str(answer)[:200]
        except:
            pass
        return cls.objects.create(question=question, value=answer, question_type=question.__class__.type_name(),
                                  interview=interview, identifier=question.identifier,
                                  as_text=cls.prep_text(as_text), as_value=cls.prep_value(as_value))

    def __unicode__(self):
        return unicode(self.as_text)

    @classmethod
    def prep_value(cls, val):
        return val

    @classmethod
    def prep_text(cls, text):
        return text

    def update(self, answer):
        self.as_text = answer
        self.as_value = answer
        self.save()

    @classmethod
    def supported_answers(cls):
        return Answer.__subclasses__()

    @classmethod
    def answer_types(cls):
        return sorted([cl.choice_name() for cl in Answer.__subclasses__() if cl is not NonResponseAnswer])

    @classmethod
    def get_class(cls, verbose_name):
        verbose_name = verbose_name.strip()
        for cl in Answer.__subclasses__():
            if cl.choice_name() == verbose_name:
                return cl
        raise ValueError('unknown class')

    def to_text(self):
        return self.value

    def pretty_print(self, as_label=False):
        return self.to_text()

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
    def fetch_contains(cls, answer_key, txt, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__icontains' % answer_key: txt})

    @classmethod
    def odk_contains(cls, node_path, value):
        return "regex(%s, '.*(%s).*')" % (node_path, value)

    @classmethod
    def equals(cls, answer, value):
        return str(answer).lower() == str(value).lower()

    @classmethod
    def fetch_equals(cls, answer_key, value, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__iexact' % answer_key: str(value)})

    @classmethod
    def odk_equals(cls, node_path, value):
        return "%s = '%s'" % (node_path, value)

    @classmethod
    def starts_with(cls, answer, txt):
        answer = answer.lower()
        txt = txt.lower()
        return answer.startswith(txt)

    @classmethod
    def fetch_starts_with(cls, answer_key, txt, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__istartswith' % answer_key: str(txt)})

    @classmethod
    def odk_starts_with(cls, node_path, value):
        return "regex(%s, '^(%s).*')" % (node_path, value)

    @classmethod
    def ends_with(cls, answer, txt):
        answer = answer.lower()
        txt = txt.lower()
        return answer.endswith(txt)

    @classmethod
    def fetch_ends_with(cls, answer_key, txt, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__iendswith' % answer_key: str(txt)})

    @classmethod
    def odk_ends_with(cls, node_path, value):
        return "regex(%s, '.*(%s)$')" % (node_path, value)

    @classmethod
    def greater_than(cls, answer, value):
        return answer > value

    @classmethod
    def fetch_greater_than(cls, answer_key, value, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__gt' % answer_key: value})

    @classmethod
    def odk_greater_than(cls, node_path, value):
        return "%s &gt; '%s'" % (node_path, value)

    @classmethod
    def less_than(cls, answer, value):
        return answer < value

    @classmethod
    def fetch_less_than(cls, answer_key, value, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__lt' % answer_key: value})

    @classmethod
    def odk_less_than(cls, node_path, value):
        return "%s &lt; '%s'" % (node_path, value)

    @classmethod
    def between(cls, answer, lowerlmt, upperlmt):
        return upperlmt > answer >= lowerlmt

    @classmethod
    def fetch_between(cls, answer_key, lowerlmt, upperlmt, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__lt' % answer_key: upperlmt, '%s__gte' % answer_key: lowerlmt})

    @classmethod
    def odk_between(cls, node_path, lowerlmt, upperlmt):
        return "(%s &gt; '%s') and (%s &lt; '%s')" % (node_path, lowerlmt, node_path, upperlmt)

    @classmethod
    def print_odk_validation(cls, node_path, validator_name, *args):
        printer = getattr(cls, 'odk_%s' % validator_name)
        return printer(node_path, *args)

    @classmethod
    def passes_test(cls, text_exp):
        return bool(eval(text_exp))

    @classmethod
    def validators(cls):
        return [cls.starts_with, cls.ends_with, cls.equals, cls.between, cls.less_than,
                cls.greater_than, cls.contains, ]

    @classmethod
    def validate_test_value(cls, value):
        '''Shall be used to validate that a given value is appropriate for this answer
        :return:
        '''
        for validator in cls._meta.get_field_by_name('value')[0].validators:
            validator(value)

    class Meta:
        app_label = 'survey'
        abstract = False
        get_latest_by = 'created'


class AutoResponse(Answer):
    """Shall be used to capture responses auto generated
    """
    value = models.CharField(null=True, max_length=100)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def prep_value(cls, val):
        return str(val).zfill(9)

    @classmethod
    def choice_name(cls):
        return 'Auto Generated'

    @classmethod
    def create(cls, interview, question, answer):
        """Anwer shall be auto prepended with interviewer name
                :param interview:
        :param question:
        :param answer:
        :return:
        """
        try:
            value = int(answer)
            prefix = 'flow-test'
            if interview.interview_channel:
                prefix = interview.interview_channel.user_identifier
            text_value = '%s-%s' % (prefix, cls.prep_value(value))    # zero fill to 1billion
        except Exception:
            raise
        return super(AutoResponse, cls).create(interview, question, answer,
                                               as_text=value, as_value=text_value)


class NumericalAnswer(Answer):
    value = models.PositiveIntegerField(null=True)

    @classmethod
    def validators(cls):
        return [cls.greater_than, cls.equals, cls.less_than, cls.between]

    @classmethod
    def create(cls, interview, question, answer):
        try:
            value = int(answer)
            text_value = cls.prep_value(value)    # zero fill to 1billion
        except Exception:
            raise
        return super(NumericalAnswer, cls).create(interview, question, answer,
                                                  as_text=value, as_value=text_value)

    @classmethod
    def prep_value(cls, val):
        return str(val).zfill(9)

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

    @classmethod
    def validate_test_value(cls, value):
        try:
            int(value)
        except ValueError, ex:
            raise ValidationError([unicode(ex), ])

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
    value = models.CharField(max_length=200, blank=False, null=False)

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
            if str(answer).isdigit():
                answer = int(answer)
                answer = question.options.get(order=answer)
            else:
                answer = question.options.get(text__iexact=answer)
        except:
            pass
        return super(MultiChoiceAnswer, cls).create(interview, question, answer,
                                                    as_text=answer.text, as_value=answer.order)

    def update(self, answer):
        try:
            if str(answer).isdigit():
                answer = int(answer)
                answer = self.options.get(order=answer)
            else:
                answer = self.options.get(text__iexact=answer)
        except:
            pass
        self.as_text = answer.text
        self.as_value = answer.order
        self.value = answer
        self.save()

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.equals, ]

    def to_text(self):
        return self.value.text

    def pretty_print(self, as_label=False):
        if as_label:
            return self.value.order
        else:
            return self.value.text

    @classmethod
    @static_var('label', 'Equals Option')
    def equals(cls, answer, txt):
        return super(MultiChoiceAnswer, cls).equals(answer, txt)


class MultiSelectAnswer(Answer):
    value = models.ManyToManyField("QuestionOption", )

    @classmethod
    def create(cls, interview, question, answer):
        raw_answer = answer
        if isinstance(answer, basestring):
            answer = answer.split(' ')
        if isinstance(answer, list):
            selected = [a.lower() for a in answer]
            options = question.options.all()
            chosen = [op.pk for op in options if op.text.lower() in selected]
            selected = question.options.filter(pk__in=chosen)
        else:
            selected = answer
        ans = cls.objects.create(question=question, question_type=question.__class__.type_name(),
                                 interview=interview, identifier=question.identifier,
                                 as_text=raw_answer, as_value=raw_answer)
        for opt in selected:
            ans.value.add(opt)
        return ans

    class Meta:
        app_label = 'survey'
        abstract = False

    def to_text(self):
        texts = []
        map(lambda opt: texts.append(opt.text), self.value.all())
        return ' and '.join(texts)

    def to_label(self):
        texts = []
        map(lambda opt: texts.append(str(opt.order)), self.value.all())
        return ' and '.join(texts)

    def pretty_print(self, as_label=False):
        if as_label:
            return self.to_label()
        else:
            return self.to_text()

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
        raw_answer = answer
        if isinstance(answer, basestring):
            answer = extract_date(answer)
        return super(DateAnswer, cls).create(interview, question, answer,
                                             as_text=raw_answer, as_value=raw_answer)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.greater_than, cls.equals, cls.less_than, cls.between]

    @classmethod
    def validate_test_value(cls, value):
        '''Shall be used to validate that a given value is appropriate for this answer
        :return:
        '''
        try:
            extract_date(value, fuzzy=True)
        except ValueError, ex:
            raise ValidationError([unicode(ex), ])


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
        raw_answer = answer
        if isinstance(answer, basestring):
            answer = answer.split(' ')
            answer = ODKGeoPoint.objects.create(latitude=answer[0], longitude=answer[1],
                                                altitude=answer[2], precision=answer[3])
        return super(GeopointAnswer, cls).create(interview, question, answer,
                                                 as_text=raw_answer, as_value=raw_answer)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.equals]

    def to_text(self):
        return ''


class NonResponseAnswer(BaseModel):
    interview = models.ForeignKey(Interview, related_name='non_response_answers', db_index=True)
    value = models.CharField(max_length=200, blank=False, null=False)
    interviewer = models.ForeignKey(
        "Interviewer", null=True, related_name='non_response_answers')

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []


class AnswerAccessDefinition(BaseModel):
    ACCESS_CHANNELS = [(name, name)
                       for name in InterviewerAccess.access_channels()]
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
    def access_channels(cls, answer_type):
        return set(AnswerAccessDefinition.objects.filter(answer_type=answer_type).values_list('channel', flat=True))

    @classmethod
    def answer_types(cls, channel):
        return set(AnswerAccessDefinition.objects.filter(channel=channel).values_list('answer_type', flat=True))