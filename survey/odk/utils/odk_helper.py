from datetime import date, datetime
import decimal
import os
import re
import copy
import zipfile
import pytz
from lxml import etree
from collections import OrderedDict
from django.http import HttpResponse, HttpResponseNotFound, StreamingHttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.files.storage import get_storage_class
from django.conf import settings
from django.shortcuts import render
from django import template
from django.utils import timezone
from survey.templatetags.template_tags import get_node_path
from django.db import transaction
from django.shortcuts import get_object_or_404
from djangohttpdigest.digest import Digestor, parse_authorization_header
from djangohttpdigest.authentication import SimpleHardcodedAuthenticator
from django.utils.translation import ugettext as _
from survey.models import Survey, Interviewer, Interview, SurveyAllocation, ODKAccess, QuestionSet, \
    Question, Batch, ODKSubmission, ODKGeoPoint, TextAnswer, Answer, NonResponseAnswer, \
    VideoAnswer, AudioAnswer, ImageAnswer, MultiSelectAnswer, MultiChoiceAnswer, DateAnswer, GeopointAnswer
from survey.odk.utils.log import logger
from functools import wraps
from survey.utils.zip import InMemoryZip
from django.contrib.sites.models import Site
from dateutils import relativedelta
from django.db.utils import IntegrityError
from django_rq import job, get_connection
from survey.templatetags.template_tags import get_xform_relative_path, get_node_path


OPEN_ROSA_VERSION_HEADER = 'X-OpenRosa-Version'
HTTP_OPEN_ROSA_VERSION_HEADER = 'HTTP_X_OPENROSA_VERSION'
OPEN_ROSA_VERSION = '1.0'
DEFAULT_CONTENT_TYPE = 'text/xml; charset=utf-8'
INSTANCE_ID_PATH = '//qset/meta/instanceID'
FORM_ID_PATH = '//qset/@id'
# ONLY_HOUSEHOLD_PATH = '//qset/onlyHousehold'
FORM_TYPE_PATH = '//qset/type'
FORM_ASSIGNMENT_PATH = '//qset/surveyAllocation'
ANSWER_NODE_PATH = '//qset/qset{{ qset_id }}'
# default content length for submission requests
DEFAULT_CONTENT_LENGTH = 10000000
MAX_DISPLAY_PER_COLLECTOR = 1000


class NotEnoughData(ValueError):
    pass


def _get_tree_from_blob(blob_contents):
    return etree.fromstring(blob_contents)


def _get_tree(xml_file):
    return etree.fromstring(xml_file.read())


# either tree or xml_string must be defined
def _get_nodes(search_path, tree=None, xml_string=None):
    if tree is None:
        tree = etree.fromstring(xml_string)
    try:
        return tree.xpath(search_path)
    except Exception, ex:
        logger.error('Error retrieving path: %s, Desc: %s' %
                     (search_path, str(ex)))


@job('odk', connection=get_connection())
def process_answers(xml, qset, access_channel, question_map, survey_allocation, submission):
    """Process answers for this answers_node. It's supposed to handle for all question answers in this xform.
    :param answers_node:
    :param qset:
    :param interviewer:
    :param question_map:
    :param survey_allocation:
    :return:
    """
    survey_tree = _get_tree_from_blob(xml)
    answers_node = _get_answer_node(survey_tree, qset)
    answers = []
    survey = survey_allocation.survey
    map(lambda node: answers.extend(get_answers(_get_nodes('./questions', node)[0], qset, question_map)),
        answers_node.getchildren())
    if survey.has_sampling and survey.sample_size > len(answers):
        raise NotEnoughData()
    save_answers(qset, access_channel, question_map, answers, survey_allocation)
    submission.status = ODKSubmission.COMPLETED
    submission.save()


def get_answers(node, qset, question_map):
    """get answers for the node set. Would work for nested loops but for loops sitting in same inline question thread
    """
    answers = []
    inline_record = {}
    for e in node.getchildren():
        if e.getchildren():
            loop_answers = get_answers(e, qset, question_map)
            _update_loop_answers(inline_record, loop_answers)
            answers.extend(loop_answers)
        else:
            inline_record[e.tag.strip('q')] = e.text
            question = question_map.get(e.tag.strip('q'), '')
            if question:
                _update_answer_dict(question, e.text, answers)
    if len(answers) == 0:
        answers.append(inline_record)
    return answers


def save_answers(qset, access_channel, question_map, answers, survey_allocation):
    survey = survey_allocation.survey
    ea = survey_allocation.allocation_ea
    interviewer = access_channel.interviewer

    def _save_record(record):
        interview = Interview.objects.create(survey=survey, question_set=qset,
                                             ea=ea,
                                             interviewer=interviewer,
                                             interview_channel=access_channel,
                                             closure_date=timezone.now())
        map(lambda (q_id, answer): _save_answer(interview, q_id, answer), record.items())

    def _save_answer(interview, q_id, answer):
        question = question_map.get(q_id, None)
        if question:
            answer_class = Answer.get_class(question.answer_type)
            answer_class.create(interview, question, answer)
    map(_save_record, answers)


def _update_answer_dict(question, answer, answers):
    for d in answers:
        d[question.pk] = answer
    return answers


def _update_loop_answers(inline_record, loop_answers):
    for record in loop_answers:
        record.update(inline_record)
    return loop_answers


def _get_answer_node(tree, qset):
    answer_path = template.Template(ANSWER_NODE_PATH).render(template.Context({'qset_id': qset.pk}))
    return _get_nodes(answer_path, tree)[0]


def _get_instance_id(survey_tree):
    return _get_nodes(INSTANCE_ID_PATH, tree=survey_tree)[0].text


def _get_form_id(survey_tree):
    return _get_nodes(FORM_ID_PATH, tree=survey_tree)


def _get_qset(survey_tree):
    pk = _get_nodes(FORM_ID_PATH, tree=survey_tree)[0]
    return QuestionSet.get(pk=pk)


def _get_allocation(survey_tree):
    pk = _get_nodes(FORM_ASSIGNMENT_PATH, tree=survey_tree)[0].text
    return SurveyAllocation.objects.get(pk=pk)


def _get_form_type(survey_tree):
    return int(_get_nodes(FORM_TYPE_PATH, tree=survey_tree)[0].text)


def process_submission(interviewer, xml_file, media_files=[], request=None):
    """extracts and saves the collected data from associated xform.
    """
    media_files = dict([(os.path.basename(f.name), f) for f in media_files])
    xml_blob = xml_file.read()
    survey_tree = _get_tree_from_blob(xml_blob)
    form_id = _get_form_id(survey_tree)
    instance_id = _get_instance_id(survey_tree)
    description = ''
    qset = _get_qset(survey_tree)
    survey_allocation = _get_allocation(survey_tree)
    # first things first. save the submission incase all else background task fails... enables recover
    submission = ODKSubmission.objects.create(interviewer=interviewer, survey=survey_allocation.survey,
                                              question_set=qset, ea=survey_allocation.allocation_ea, form_id=form_id,
                                              xml=xml_blob, instance_id=instance_id)
    question_map = dict([(str(q.pk), q) for q in qset.flow_questions])
    access_channel = ODKAccess.objects.get(interviewer=interviewer)
    # process_answers.delay(xml_blob, qset, interviewer, question_map, survey_allocation, submission)
    process_answers(xml_blob, qset, access_channel, question_map, survey_allocation, submission)
    return submission


def get_survey(interviewer):
    return SurveyAllocation.get_allocation(interviewer)


def get_survey_allocation(interviewer):
    '''Just helper function to put additional layer of abstraction to allocation retrival
    @param: interviewer. Interviewer to which to get survey allocation
    '''
    return SurveyAllocation.get_allocation_details(interviewer)


def disposition_ext_and_date(name, extension, show_date=True):
    if name is None:
        return 'attachment;'
    if show_date:
        name = "%s_%s" % (name, date.today().strftime("%Y_%m_%d"))
    return 'attachment; filename=%s.%s' % (name, extension)


def response_with_mimetype_and_name(
        mimetype, name, extension=None, show_date=True, file_path=None,
        use_local_filesystem=False, full_mime=False):
    if extension is None:
        extension = mimetype
    if not full_mime:
        mimetype = "application/%s" % mimetype
    if file_path:
        try:
            if not use_local_filesystem:
                default_storage = get_storage_class()()
                wrapper = FileWrapper(default_storage.open(file_path))
                response = StreamingHttpResponse(wrapper, mimetype=mimetype)
                response['Content-Length'] = default_storage.size(file_path)
            else:
                wrapper = FileWrapper(open(file_path))
                response = StreamingHttpResponse(wrapper, mimetype=mimetype)
                response['Content-Length'] = os.path.getsize(file_path)
        except IOError:
            response = HttpResponseNotFound(
                _(u"The requested file could not be found."))
    else:
        response = HttpResponse(content_type=mimetype)
    response['Content-Disposition'] = disposition_ext_and_date(
        name, extension, show_date)
    return response


class HttpResponseNotAuthorized(HttpResponse):
    status_code = 401

    def __init__(self):
        HttpResponse.__init__(self)
        self['WWW-Authenticate'] =\
            'Basic realm="%s"' % Site.objects.get_current().name


class BaseOpenRosaResponse(HttpResponse):
    status_code = 201

    def __init__(self, *args, **kwargs):
        super(BaseOpenRosaResponse, self).__init__(*args, **kwargs)
        if self.status_code > 201:
            self.reason_phrase = self.content
        self[OPEN_ROSA_VERSION_HEADER] = OPEN_ROSA_VERSION
        tz = pytz.timezone(settings.TIME_ZONE)
        dt = datetime.now(tz).strftime('%a, %d %b %Y %H:%M:%S %Z')
        self['Date'] = dt
        self['X-OpenRosa-Accept-Content-Length'] = DEFAULT_CONTENT_LENGTH
        self['Content-Type'] = DEFAULT_CONTENT_TYPE


class OpenRosaResponse(BaseOpenRosaResponse):
    status_code = 201

    def __init__(self, *args, **kwargs):
        super(OpenRosaResponse, self).__init__(*args, **kwargs)
        # wrap content around xml
        self.content = '''<?xml version='1.0' encoding='UTF-8' ?>
<OpenRosaResponse xmlns="http://openrosa.org/http/response">
        <message nature="">%s</message>
</OpenRosaResponse>''' % self.content
        self['X-OpenRosa-Accept-Content-Length'] = len(self.content)


class OpenRosaResponseNotFound(OpenRosaResponse):
    status_code = 404


class OpenRosaResponseBadRequest(OpenRosaResponse):
    status_code = 400


class OpenRosaResponseNotAllowed(OpenRosaResponse):
    status_code = 405


class OpenRosaRequestForbidden(OpenRosaResponse):
    status_code = 403


class OpenRosaRequestConflict(OpenRosaResponse):
    status_code = 409


class OpenRosaServerError(OpenRosaResponse):
    status_code = 500


def http_basic_interviewer_auth(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.has_key('HTTP_AUTHORIZATION'):
            authmeth, auth = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
            logger.debug('request meta: %s' %
                         request.META['HTTP_AUTHORIZATION'])
            if authmeth.lower() == 'basic':
                auth = auth.strip().decode('base64')
                username, password = auth.split(':', 1)
                try:
                    request.user = ODKAccess.objects.get(
                        user_identifier=username, odk_token=password, is_active=True).interviewer
                    #Interviewer.objects.get(mobile_number=username, odk_token=password)
                    return func(request, *args, **kwargs)
                except ODKAccess.DoesNotExist:
                    return OpenRosaResponseNotFound()
        return HttpResponseNotAuthorized()
    return _decorator


def http_digest_interviewer_auth(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.has_key('HTTP_HOST'):
            realm = request.META['HTTP_HOST']
        else:
            realm = Site.objects.get_current().name
        digestor = Digestor(method=request.method,
                            path=request.get_full_path(), realm=realm)
        if request.META.has_key('HTTP_AUTHORIZATION'):
            logger.debug('request meta: %s' %
                         request.META['HTTP_AUTHORIZATION'])
            try:
                parsed_header = digestor.parse_authorization_header(
                    request.META['HTTP_AUTHORIZATION'])
                if parsed_header['realm'] == realm:
                    odk_access = ODKAccess.objects.get(user_identifier=parsed_header[
                                                       'username'], is_active=True)
                    # interviewer = Interviewer.objects.get(mobile_number=parsed_header['username'], is_blocked=False)
                    authenticator = SimpleHardcodedAuthenticator(server_realm=realm,
                                                                 server_username=odk_access.user_identifier,
                                                                 server_password=odk_access.odk_token)
                    if authenticator.secret_passed(digestor):
                        request.user = odk_access.interviewer
                        return func(request, *args, **kwargs)
            except ODKAccess.DoesNotExist:
                return OpenRosaResponseNotFound()
            except ValueError, err:
                return OpenRosaResponseBadRequest()
        response = HttpResponseNotAuthorized()
        response['www-authenticate'] = digestor.get_digest_challenge()
        return response
    return _decorator


def get_zipped_dir(dirpath):
    zipf = InMemoryZip()
    for root, dirs, files in os.walk(dirpath):
        for filename in files:
            f = open(os.path.join(root, filename))
            zipf.append(filename, f.read())
            f.close()
    return zipf.read()
