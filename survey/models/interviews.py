import os
import string
import time
from django.core.files.base import ContentFile
from datetime import datetime
from django_rq import job
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil.parser import parse as extract_date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from survey.utils.logger import glogger as logger
from survey.models.base import BaseModel
from survey.models.access_channels import InterviewerAccess, ODKAccess, USSDAccess
from survey.models.locations import Point
from survey.utils.decorators import static_var


class Interview(BaseModel):
    interviewer = models.ForeignKey(
        "Interviewer",
        null=True,
        related_name="interviews")  # nullable for simulation & backend load
    ea = models.ForeignKey('EnumerationArea', related_name='interviews',
                           db_index=True, null=True)  # repeated here for easy reporting
    survey = models.ForeignKey(
        'Survey',
        related_name='interviews',
        db_index=True,
        null=True)
    question_set = models.ForeignKey(
        'QuestionSet',
        related_name='interviews',
        db_index=True)
    interview_reference = models.ForeignKey(
        'Interview',
        related_name='follow_up_interviews',
        null=True,
        blank=True)
    interview_channel = models.ForeignKey(
        InterviewerAccess, related_name='interviews', null=True)
    closure_date = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='Completion Date')
    # just used to capture preview/data entry tester
    uploaded_by = models.ForeignKey(User, null=True, blank=True)
    test_data = models.BooleanField(default=False)
    #instance_id = models.CharField(max_length=200, null=True, blank=True)
    last_question = models.ForeignKey("Question", related_name='ongoing', null=True, blank=True)

    def __unicode__(self):
        return '%s: %s' % (self.id, self.question_set.name)

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
        answer_class = Answer.get_class(question.answer_type)
        answers = answer_class.objects.filter(interview=self, question=question)
        if answers.exists():
            reply = unicode(answers[0].to_text())
            if capwords:
                reply = string.capwords(reply)
            return reply
        return ''

    @classmethod
    def save_answers(cls, qset, survey, ea, access_channel, question_map, answers, survey_parameters={},
                     reference_interview=None, media_files={}):
        """Used to save a dictionary list of answers. keys in each answer dict must be keys in the question map
        :param qset:
        :param survey:
        :param ea:
        :param access_channel:
        :param question_map: For convinence, a dictionary containing ID to question instance {1: quest1, 2: quest2... }
        :param answers: list of dictionaries each contains the [{quest_id: answer, quest_id2: answer2, ...}, ]
        :param survey_parameters: This is a dictionary of group paramaters
        :param reference_interview: Reference interview if any
        :param media_files: Any media files available. Required for file related answers (Image, audio and video)
        :return:
        """
        # at least make sure this qset is covered
        question_map.update({question.id: question for question in qset.all_questions})
        interviewer = access_channel.interviewer
        interviews = []
        if reference_interview and (isinstance(reference_interview, Interview) is False):
            reference_interview = Interview.get(id=reference_interview)

        def _save_record(record):
            now = timezone.now()
            closure_date = record.get('completion_date', now).replace(tzinfo=now.tzinfo)
            interview = Interview.objects.create(survey=survey, question_set=qset,
                                                 ea=ea, interviewer=interviewer, interview_channel=access_channel,
                                                 closure_date=closure_date,
                                                 interview_reference=reference_interview)
            interviews.append(interview)
            map(lambda (q_id, answer): _save_answer(interview, q_id, answer), record.items())
            if survey_parameters:
                map(lambda (q_id, answer): _save_answer(interview, q_id, answer), survey_parameters.items())

        def _save_answer(interview, q_id, answer):
            try:
                question = question_map.get(q_id, None)
                if question and answer:
                    answer_class = Answer.get_class(question.answer_type)
                    if question.answer_type in [AudioAnswer.choice_name(), ImageAnswer.choice_name(),
                                                VideoAnswer.choice_name()]:
                        media = media_files.get(answer, None)
                        # only file objects or the file contents
                        answer = ContentFile(media, name=answer)
                    answer_class.create(interview, question, answer)
            except Exception, ex:
                logger.error('error saving %s, desc: %s' % (q_id, str(ex)))
        map(_save_record, answers)
        return interviews

    def respond(self, reply=None, channel=ODKAccess.choice_name(), answers_context={}):
        """
            Respond to given reply for specified channel. Irrespective to group.
            Might be depreciating group in the near future
            This method is volatile.Raises exception if some error happens in the process
        :param reply:
        :param channel:
        :return: Returns next question if any
        """
        qset = self.question_set.to_exact
        if self.is_closed():
            return
        next_question = None
        if self.has_started and reply:
            # save reply
            answer_class = Answer.get_class(self.last_question.answer_type)
            answer_class.create(self, self.last_question, reply)
            # compute nnext
            next_question = self.last_question.next_question(reply)
        elif self.has_started is False:
            self.last_question = qset.g_first_question
            self.save()
            reply = None        # ignore the initial message
        if self.has_started and reply is None:
            return self.last_question.display_text(channel=channel, context=answers_context)
        # now confirm the question is applicable
        if next_question and AnswerAccessDefinition.is_valid(channel, next_question.answer_type) is False:
            # if not get next line question
            next_question = qset.next_inline(self.last_question, channel=channel)
        response_text = None
        if next_question:
            self.last_question = next_question
            response_text = self.last_question.display_text(channel=channel, context=answers_context)
        else:
            self.closure_date = timezone.now()
        self.save()
        return response_text

    @classmethod
    def interviews_in(cls, location, survey=None, include_self=False):
        left = location.lft
        right = location.rght
        if include_self is False:
            left = left + 1
            right = right - 1
        kwargs = {'ea__locations__lft__gte': left, 'ea__locations__lft__lte': right,
                  'ea__locations__level__gte': location.level}
        if survey:
            kwargs['survey'] = survey
        return Interview.objects.filter(**kwargs)

    @classmethod
    def interviews(cls, survey):
        return Interview.objects.filter(survey=survey)

    class Meta:
        app_label = 'survey'


class Answer(BaseModel):
    STRING_FILL_LENGTH = 20
    # now question_type is used to store the exact question we are answering
    # (Listing, Batch, personal info)
    # I think using generic models is an overkill since they're all
    question_type = models.CharField(max_length=100)
    # questions
    interview = models.ForeignKey(
        Interview,
        related_name='%(class)s',
        db_index=True)
    question = models.ForeignKey(
        "Question",
        null=True,
        related_name="%(class)s",
        on_delete=models.PROTECT,
        db_index=True)
    # basically calculated field for reporting
    identifier = models.CharField(max_length=200, db_index=True)
    # basically calculated field for reporting
    as_text = models.CharField(max_length=200, db_index=True)
    # basically calculated field for reporting
    as_value = models.CharField(max_length=200, db_index=True)

    @classmethod
    def create(cls, interview, question, answer, as_text=None, as_value=None):
        if as_text is None:
            as_text = cls.prep_text(unicode(answer)[:200])
        if as_value is None:
            as_value = cls.prep_value(unicode(answer)[:200])
        return cls.objects.create(
            question=question,
            value=answer,
            question_type=question.__class__.type_name(),
            interview=interview,
            identifier=question.identifier,
            as_text=as_text,
            as_value=as_value)

    def __unicode__(self):
        return unicode(self.as_text)

    @classmethod
    def prep_value(cls, val):
        return unicode(val).lower()

    @classmethod
    def prep_text(cls, text):
        return unicode(text).lower()

    def update(self, answer):
        self.as_text = answer
        self.as_value = answer
        self.save()

    @classmethod
    def supported_answers(cls):
        supported = [cl for cl in Answer.__subclasses__() if cl not in [NonResponseAnswer, NumericalTypeAnswer]]
        supported.extend([cl for cl in NumericalTypeAnswer.__subclasses__()])
        return supported

    @classmethod
    def answer_types(cls):
        answer_types = [cl.choice_name() for cl in Answer.__subclasses__() if cl not in [NonResponseAnswer,
                                                                                         NumericalTypeAnswer]]
        answer_types.extend([cl.choice_name() for cl in NumericalTypeAnswer.__subclasses__()])
        return sorted(answer_types)

    @classmethod
    def get_class(cls, verbose_name):
        verbose_name = verbose_name.strip()
        for cl in Answer.__subclasses__():
            if cl.choice_name() == verbose_name:
                return cl
        # check in numerical answer type
        for cl in NumericalTypeAnswer.__subclasses__():
            if cl.choice_name() == verbose_name:
                return cl
        raise ValueError('unknown class %s' % verbose_name)

    def to_text(self):
        return self.as_text

    def to_label(self):
        return self.as_value

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
        txt = cls.prep_value(txt)
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__icontains' % answer_key: txt})

    @classmethod
    def odk_contains(cls, node_path, value):
        return "regex(%s, '.*(%s).*')" % (node_path, value)

    @classmethod
    def equals(cls, answer, value):
        return unicode(answer).lower() == unicode(value).lower()

    @classmethod
    def fetch_equals(cls, answer_key, value, qs=None):
        value = cls.prep_value(value)
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__iexact' % answer_key: unicode(value)})

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
        txt = cls.prep_value(txt)
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__istartswith' % answer_key: unicode(txt)})

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
        txt = cls.prep_value(txt)
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__iendswith' % answer_key: unicode(txt)})

    @classmethod
    def odk_ends_with(cls, node_path, value):
        return "regex(%s, '.*(%s)$')" % (node_path, value)

    @classmethod
    def greater_than(cls, answer, value):
        return answer > value

    @classmethod
    def fetch_greater_than(cls, answer_key, value, qs=None):
        value = cls.prep_value(value)
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
        value = cls.prep_value(value)
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
    def get_validation_query_params(cls):
        return {cls.greater_than.__name__: 'gt', cls.less_than.__name__: 'lt',
                cls.starts_with.__name__: 'istartswith', cls.ends_with.__name__: 'iendswith',
                cls.contains.__name__: 'icontains', cls.equals.__name__: 'iexact'}

    @classmethod
    def get_validation_queries(cls, method_name, answer_key, *test_args, **kwargs):
        namespace = kwargs.pop('namespace', '')
        validation_queries = cls.get_validation_query_params()
        if method_name == cls.between.__name__:         # only between takes two arguments
            query_args = []
            return {'%s%s__%s' % (namespace, answer_key, validation_queries[cls.less_than.__name__]): test_args[1],
                    '%s%s__%s' % (namespace, answer_key,
                                  validation_queries[cls.greater_than.__name__]): test_args[0]
                    }
        else:
            return {'%s%s__%s' % (namespace, answer_key, validation_queries[method_name]): test_args[0],}
    # 
    # @classmethod
    # def __getattr__(cls, name):
    #     """Shall be used to implement all fetch_validation function methods.
    #     This is required instead of implementing individual code for each. This function results in db call
    #     :param name:
    #     :return:
    #     """
    #     if name.startswith('fetch_'):
    #         method_name = name[6:]
    # 
    #         def wrapper(answer_key, qs=cls.objects, *test_args):
    #             return qs.filter(**cls.get_validation_queries(method_name, answer_key, *test_args))
    #         return wrapper
    #     raise AttributeError

    @classmethod
    def fetch_between(cls, answer_key, lowerlmt, upperlmt, qs=None):
        upperlmt = cls.prep_value(upperlmt)
        lowerlmt = cls.prep_value(lowerlmt)
        if qs is None:
            qs = cls.objects
        return qs.filter(**{'%s__lt' % answer_key: upperlmt, '%s__gte' % answer_key: lowerlmt})

    @classmethod
    def odk_between(cls, node_path, lowerlmt, upperlmt):
        return "(%s &gt; '%s') and (%s &lt;= '%s')" % (node_path, lowerlmt, node_path, upperlmt)

    @classmethod
    def print_odk_validation(cls, node_path, validator_name, *args):
        printer = getattr(cls, 'odk_%s' % validator_name)
        return printer(node_path, *args)

    @classmethod
    def passes_test(cls, text_exp):
        return bool(eval(text_exp))

    @classmethod
    def validators(cls):
        return [
            cls.starts_with,
            cls.ends_with,
            cls.equals,
            cls.between,
            cls.less_than,
            cls.greater_than,
            cls.contains,
        ]

    @classmethod
    def validate_test_value(cls, value):
        """Shall be used to validate that a given value is appropriate for this answer
        :return:
        """
        for validator in cls._meta.get_field_by_name('value')[0].validators:
            validator(value)

    class Meta:
        app_label = 'survey'
        abstract = False
        get_latest_by = 'created'


class NumericalTypeAnswer(Answer):

    @classmethod
    def validators(cls):
        return [
            cls.equals,
            cls.between,
            cls.less_than,
            cls.greater_than,
        ]

    @classmethod
    def prep_text(cls, val):
        return unicode(val).zfill(cls.STRING_FILL_LENGTH)

    @classmethod
    def prep_value(cls, val):
        return unicode(val).zfill(cls.STRING_FILL_LENGTH)

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
        return "(%s &gt; %s) and (%s &lt;= %s)" % (
            node_path, lowerlmt, node_path, upperlmt)

    @classmethod
    def validate_test_value(cls, value):
        try:
            int(value)
        except ValueError as ex:
            raise ValidationError([unicode(ex), ])

    class Meta:
        app_label = 'survey'
        abstract = True


class NumericalAnswer(NumericalTypeAnswer):
    value = models.PositiveIntegerField(null=True)

    @classmethod
    def create(cls, interview, question, answer):
        value = int(answer)
        text_value = cls.prep_value(value)    # zero fill to 1billion
        return super(NumericalAnswer, cls).create(interview, question, answer, as_text=value, as_value=text_value)

    class Meta:
        app_label = 'survey'
        abstract = False


class AutoResponse(NumericalTypeAnswer):
    """Shall be used to capture responses auto generated
    """
    value = models.CharField(null=True, max_length=100)

    @classmethod
    def choice_name(cls):
        return 'Auto Generated'

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def create(cls, interview, question, answer):
        """Anwer shall be auto prepended with interviewer name
                :param interview:
        :param question:
        :param answer:
        :return:
        """
        value = int(answer)
        prefix = 'flow-test'
        if interview.interview_channel:
            prefix = interview.interview_channel.user_identifier
        # zero fill to 1billion
        text_value = '%s-%s' % (prefix, cls.prep_value(value))
        return super(
            AutoResponse,
            cls).create(
            interview,
            question,
            answer,
            as_text=value,
            as_value=text_value)


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
        if unicode(answer).isdigit():
            answer = int(answer)
            answer = question.options.get(order=answer)
        else:
            answer = question.options.get(text__iexact=answer)
        return super(
            MultiChoiceAnswer,
            cls).create(
            interview,
            question,
            answer,
            as_text=answer.text,
            as_value=answer.order)

    def update(self, answer):
        if unicode(answer).isdigit():
            answer = int(answer)
            answer = self.question.options.get(order=answer)
        else:
            answer = self.question.options.get(text__iexact=answer)
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
            raw_answer = ' '.join(answer.values_list('text', flat=True))
        ans = cls.objects.create(
            question=question,
            question_type=question.__class__.type_name(),
            interview=interview,
            identifier=question.identifier,
            as_text=raw_answer,
            as_value=raw_answer)
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
        map(lambda opt: texts.append(unicode(opt.order)), self.value.all())
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
        return answer.lower() == txt.lower()


class DateAnswer(Answer):
    value = models.DateField(null=True)

    @classmethod
    def prep_value(cls, val):
        if isinstance(val, basestring):
            val = extract_date(val, dayfirst=False)
        # prepare as integer. for saving
        date_value = int(time.mktime(val.timetuple()))
        return unicode(date_value).zfill(cls.STRING_FILL_LENGTH)

    @classmethod
    def create(cls, interview, question, answer):
        raw_answer = answer
        if isinstance(answer, basestring):
            answer = extract_date(answer, dayfirst=False)
        # use zfill to normalize the string for comparism
        return super(DateAnswer, cls).create(interview, question, answer, as_text=raw_answer,
                                             as_value=cls.prep_value(answer)
                                             )

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.greater_than, cls.equals, cls.less_than, cls.between]

    @classmethod
    def greater_than(cls, answer, value):
        if isinstance(value, basestring):
            value = extract_date(value, dayfirst=True).date()
        if isinstance(answer, basestring):
            answer = extract_date(answer, dayfirst=True).date()
        return answer > value

    @classmethod
    def less_than(cls, answer, value):
        if isinstance(value, basestring):
            value = extract_date(value, dayfirst=True).date()
        if isinstance(answer, basestring):
            answer = extract_date(answer, dayfirst=True).date()
        return answer < value

    @classmethod
    def between(cls, answer, lowerlmt, upperlmt):
        if isinstance(answer, basestring):
            answer = extract_date(answer, dayfirst=True).date()
        if isinstance(lowerlmt, basestring):
            lowerlmt = extract_date(lowerlmt, dayfirst=True).date()
        if isinstance(upperlmt, basestring):
            upperlmt = extract_date(upperlmt, dayfirst=True).date()
        return upperlmt > answer >= lowerlmt

    @classmethod
    def to_odk_date(cls, date_val):
        if isinstance(date_val, basestring):
            date_val = extract_date(date_val, dayfirst=True)
        return "date('%s')" % date_val.strftime('%Y-%m-%d')

    @classmethod
    def odk_greater_than(cls, node_path, value):
        return "%s &gt; %s" % (node_path, cls.to_odk_date(value))

    @classmethod
    def odk_less_than(cls, node_path, value):
        return "%s &lt; %s" % (node_path, cls.to_odk_date(value))

    @classmethod
    def odk_between(cls, node_path, lowerlmt, upperlmt):
        return "(%s &gt; %s) and (%s &lt;= %s)" % (
            node_path, cls.to_odk_date(lowerlmt), node_path, cls.to_odk_date(upperlmt))

    @classmethod
    def validate_test_value(cls, value):
        '''Shall be used to validate that a given value is appropriate for this answer
        :return:
        '''
        try:
            extract_date(value, fuzzy=True)
        except ValueError as ex:
            raise ValidationError([unicode(ex), ])


class FileAnswerMixin(object):
    @classmethod
    def create(cls, interview, question, answer, as_text=None, as_value=None):
            # answer is a file object
        as_value = os.path.basename(answer.name)
        as_text = os.path.basename(answer.name)
        return cls.objects.create(
            question=question,
            value=answer,
            question_type=question.__class__.type_name(),
            interview=interview,
            identifier=question.identifier,
            as_text=as_text,
            as_value=as_value)


class AudioAnswer(FileAnswerMixin, Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []


class VideoAnswer(FileAnswerMixin, Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []


class ImageAnswer(FileAnswerMixin, Answer):
    value = models.FileField(upload_to=settings.ANSWER_UPLOADS, null=True)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []


class GeopointAnswer(Answer):
    value = models.ForeignKey(ODKGeoPoint, null=True)

    @classmethod
    def create(cls, interview, question, answer):
        raw_answer = answer
        if isinstance(answer, basestring):
            answer = answer.split(' ')
            answer = ODKGeoPoint.objects.create(
                latitude=answer[0],
                longitude=answer[1],
                altitude=answer[2],
                precision=answer[3])
        return super(
            GeopointAnswer,
            cls).create(
            interview,
            question,
            answer,
            as_text=raw_answer,
            as_value=raw_answer)

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return [cls.equals, ]


class NonResponseAnswer(BaseModel):
    interview = models.ForeignKey(
        Interview,
        related_name='non_response_answers',
        db_index=True)
    value = models.CharField(max_length=200, blank=False, null=False)
    interviewer = models.ForeignKey(
        "Interviewer", null=True, related_name='non_response_answers')

    class Meta:
        app_label = 'survey'
        abstract = False

    @classmethod
    def validators(cls):
        return []

    @property
    def as_text(self):
        return self.value

    @property
    def as_value(self):
        return self.value


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
            return cls.objects.get(
                answer_type=answer_type,
                channel=channel) is not None
        except cls.DoesNotExist:
            return False

    @classmethod
    def access_channels(cls, answer_type):
        return set(AnswerAccessDefinition.objects.filter(answer_type=answer_type).values_list('channel', flat=True))

    @classmethod
    def answer_types(cls, channel):
        """Returns the answer type compatible with this channel"""
        return set(
            AnswerAccessDefinition.objects.filter(
                channel=channel).values_list(
                'answer_type', flat=True))

    @classmethod
    def reload_answer_categories(cls):
        from survey.models import USSDAccess, ODKAccess, WebAccess
        cls.objects.get_or_create(channel=USSDAccess.choice_name(),
                                                     answer_type=AutoResponse.choice_name())
        cls.objects.get_or_create(channel=USSDAccess.choice_name(),
                                                     answer_type=NumericalAnswer.choice_name())
        cls.objects.get_or_create(channel=USSDAccess.choice_name(),
                                                     answer_type=TextAnswer.choice_name())
        cls.objects.get_or_create(channel=USSDAccess.choice_name(),
                                                     answer_type=MultiChoiceAnswer.choice_name())

        # ODK definition
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=AutoResponse.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=NumericalAnswer.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=TextAnswer.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=MultiChoiceAnswer.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=MultiSelectAnswer.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=ImageAnswer.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=GeopointAnswer.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=DateAnswer.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=AudioAnswer.choice_name())
        cls.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=VideoAnswer.choice_name())

        # web form definition
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=NumericalAnswer.choice_name())
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=TextAnswer.choice_name())
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=MultiChoiceAnswer.choice_name())
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=MultiSelectAnswer.choice_name())
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=ImageAnswer.choice_name())
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=GeopointAnswer.choice_name())
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=DateAnswer.choice_name())
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=AudioAnswer.choice_name())
        cls.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=VideoAnswer.choice_name())
