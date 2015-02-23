from datetime import date, datetime
import decimal
import os
import zipfile
import pytz
from lxml import etree
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render
from django import template
from django.db import transaction
from django.shortcuts import get_object_or_404
from djangohttpdigest.digest import Digestor, parse_authorization_header
from djangohttpdigest.authentication import SimpleHardcodedAuthenticator
from django.utils.translation import ugettext as _
from survey.models import Survey, Investigator, Household, HouseholdMember, Question, Batch, ODKSubmission, ODKGeoPoint, RandomHouseHoldSelection
from survey.investigator_configs import NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR
from survey.odk.utils.log import logger
from survey.tasks import execute
from functools import wraps
from survey.utils.zip import InMemoryZip
from django.contrib.sites.models import Site


OPEN_ROSA_VERSION_HEADER = 'X-OpenRosa-Version'
HTTP_OPEN_ROSA_VERSION_HEADER = 'HTTP_X_OPENROSA_VERSION'
OPEN_ROSA_VERSION = '1.0'
DEFAULT_CONTENT_TYPE = 'text/xml; charset=utf-8'
HOUSEHOLD_MEMBER_PATH = '//survey/householdMember'
ANSWER_PATH = '//survey/b{{batch_id}}/q{{question_id}}'
INSTANCE_ID_PATH = '//survey/meta/instanceID'
FORM_ID_PATH = '//survey/@id'
MULTI_SELECT_XFORM_SEP = ' '
GEOPOINT_XFORM_SEP = ' '
# default content length for submission requests
DEFAULT_CONTENT_LENGTH = 10000000
MAX_DISPLAY_PER_COLLECTOR = 1000


def _get_tree(xml_file):
    return etree.fromstring(xml_file.read())

def _get_nodes(search_path, tree=None, xml_string=None): #either tree or xml_string must be defined
    if tree is None:
        tree = etree.fromstring(xml_string)
    try:
        return tree.xpath(search_path)
    except Exception, ex:
        logger.error('Error retrieving path: %s, Desc: %s' % (search_path, str(ex)))

def _get_household_members(survey_tree):
    member_nodes = _get_nodes(HOUSEHOLD_MEMBER_PATH, tree=survey_tree)
    return HouseholdMember.objects.filter(pk__in=[member_node.text for member_node in member_nodes]).all()

def build_answer(question, response):
    logger.info('question: %s, response: %s' % (question.pk, response))
    if question.answer_type == Question.MULTICHOICE:
        return question.options.get(pk=response)
    if question.answer_type == Question.MULTISELECT:
        return question.options.filter(pk__in=response.split(MULTI_SELECT_XFORM_SEP))
    if question.answer_type == Question.DATE:
        return datetime.strptime(response, '%Y-%m-%d')
    if question.answer_type == Question.GEOPOINT:
        answer = ODKGeoPoint()
        (answer.latitude, answer.longitude, answer.altitude, answer.precision) = response.split(GEOPOINT_XFORM_SEP)
        answer.save()
        return answer
    return response

def register_member_answer(investigator, question, household_member, answer, batch):
    answer_class = question.answer_class()
    answer = build_answer(question, answer)
    if question.answer_type == Question.MULTISELECT:
        created = answer_class.objects.create(investigator=investigator, question=question, householdmember=household_member,
                         household=household_member.household, batch=batch)
        created.answer = answer
        created.save()
    else:
        created = answer_class.objects.create(investigator=investigator, question=question, householdmember=household_member,
                         answer=answer, household=household_member.household, batch=batch)
    return created

def _get_responses(survey_tree, household_member):
    survey = household_member.household.survey
    response_dict = {}
    for batch in survey.batch.all():
        for question in batch.all_questions():
            context = template.Context({'batch_id': batch.pk, 'question_id' : question.pk})
            answer_path = template.Template(ANSWER_PATH).render(context)
            response_dict[(batch.pk, question.pk)] = _get_nodes(answer_path, tree=survey_tree)[0].text
    return response_dict
                
def _get_instance_id(survey_tree):
    return _get_nodes(INSTANCE_ID_PATH, tree=survey_tree)[0].text

def _get_form_id(survey_tree):
    return _get_nodes(FORM_ID_PATH, tree=survey_tree)[0]

@transaction.autocommit
def process_submission(investigator, xml_file, media_files=[], request=None):
    """
    extract surveys and for this xml file and for specified household member
    """
    media_files = dict([(os.path.basename(f.name), f) for f in media_files])
    reports =  []
    survey_tree = _get_tree(xml_file)
    household_members = _get_household_members(survey_tree)
    for member in household_members:
        member_completion_report = {}
        household = member.household
        if household.investigator is not investigator:
            continue #do not process current member if it does not belong to this investigator
        survey = household.survey
        response_dict = _get_responses(survey_tree, member)
        treated_batches = {}
        for (b_id, q_id), answer in response_dict.items():
            question = Question.objects.get(pk=q_id)
            batch = treated_batches.get(b_id, Batch.objects.get(pk=b_id))
            if question.answer_type in [Question.AUDIO, Question.IMAGE, Question.VIDEO]:
                answer = media_files.get(answer, None)
            created = register_member_answer(investigator, question, member, answer, batch)
            member_completion_report[(b_id, q_id)] = created
            if b_id not in treated_batches.keys():
                treated_batches[b_id] = batch
        submission = ODKSubmission.objects.create(investigator=investigator, 
                survey=survey, form_id=_get_form_id(survey_tree),
                instance_id=_get_instance_id(survey_tree), household_member=member, 
                xml=etree.tostring(survey_tree, pretty_print=True))
        submission.save_attachments(media_files.values())
#                execute.delay(submission.save_attachments, media_files)
        map(lambda batch: member.batch_completed(batch), treated_batches.values()) #create batch completion for question batches
        if member.household.completed_currently_open_batches():
            map(lambda batch: member.household.batch_completed(batch), treated_batches.values())
        reports.append(submission)
    return reports

def get_households(investigator):
    """
        return the households with uncompleted surveys for households assigned to this investigator
        #to do: Need to make this retrieval more effecient in the future
    """
    open_survey = Survey.currently_open_survey(investigator.location)
    logger.info('open surveys: %s' % open_survey)
    if open_survey.has_sampling:
        RandomHouseHoldSelection.objects.get_or_create(mobile_number=investigator.mobile_number, survey=open_survey)[0].generate(
                no_of_households=open_survey.sample_size, survey=open_survey)
        households = investigator.households.filter(ea=investigator.ea, survey=open_survey, 
				random_sample_number__isnull=False)
    else:
        households = investigator.all_households(open_survey=open_survey, non_response_reporting=True)      
    logger.info('households: %s' % investigator.households.count())
    return [household for household in households.all() if not household.survey_completed()] 


class SubmissionReport:
    form_id = None
    instance_id = None
    report_details = None

    def __init__(self, form_id, instance_id, report_details):
        self.form_id = form_id
        self.instance_id = instance_id
        self.report_details = report_details

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
        response = HttpResponse(mimetype=mimetype)
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


class OpenRosaResponseNotFound(OpenRosaResponse):
    status_code = 404


class OpenRosaResponseBadRequest(OpenRosaResponse):
    status_code = 400

class OpenRosaResponseNotAllowed(OpenRosaResponse):
    status_code = 405

def http_basic_investigator_auth(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.has_key('HTTP_AUTHORIZATION'):
            authmeth, auth = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
            logger.info('request meta: %s' % request.META['HTTP_AUTHORIZATION'])
            if authmeth.lower() == 'basic':
                auth = auth.strip().decode('base64')
                username, password = auth.split(':', 1)
                try:
                    request.user = Investigator.objects.get(mobile_number=username, odk_token=password)
                    return func(request, *args, **kwargs)
                except Investigator.DoesNotExist:
                    return OpenRosaResponseNotFound()
        return HttpResponseNotAuthorized()
    return _decorator

def http_digest_investigator_auth(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        realm = Site.objects.get_current().name
        digestor = Digestor(method=request.method, path=request.get_full_path(), realm=realm)
        if request.META.has_key('HTTP_AUTHORIZATION'):
            logger.info('request meta: %s' % request.META['HTTP_AUTHORIZATION'])
            try:
                parsed_header = digestor.parse_authorization_header(request.META['HTTP_AUTHORIZATION'])
                if parsed_header['realm'] == realm:
                    investigator = Investigator.objects.get(mobile_number=parsed_header['username'], is_blocked=False)
                    authenticator = SimpleHardcodedAuthenticator(server_realm=realm, server_username=investigator.mobile_number, server_password=investigator.odk_token)
                    request.user = investigator
                    if authenticator.secret_passed(digestor):
                        return func(request, *args, **kwargs)
            except Investigator.DoesNotExist:
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
