from datetime import date, datetime
import decimal
import os
import zipfile
import pytz
from lxml import etree
from django.http import HttpResponse, HttpResponseNotFound, StreamingHttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.files.storage import get_storage_class
from django.conf import settings
from django.shortcuts import render
from django import template
from django.db import transaction
from django.shortcuts import get_object_or_404
from djangohttpdigest.digest import Digestor, parse_authorization_header
from djangohttpdigest.authentication import SimpleHardcodedAuthenticator
from django.utils.translation import ugettext as _
from survey.models import Survey, Interviewer, Interview, SurveyAllocation, ODKAccess, Household, HouseholdMember, HouseholdHead, \
            Question, Batch, ODKSubmission, ODKGeoPoint, TextAnswer, Answer, NonResponseAnswer, \
            VideoAnswer, AudioAnswer, ImageAnswer, MultiSelectAnswer, MultiChoiceAnswer, DateAnswer, GeopointAnswer, \
            SurveyHouseholdListing, HouseholdListing
from survey.interviewer_configs import NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER
from survey.odk.utils.log import logger
from survey.tasks import execute
from functools import wraps
from survey.utils.zip import InMemoryZip
from django.contrib.sites.models import Site
from dateutils import relativedelta
from django.db.utils import IntegrityError


OPEN_ROSA_VERSION_HEADER = 'X-OpenRosa-Version'
HTTP_OPEN_ROSA_VERSION_HEADER = 'HTTP_X_OPENROSA_VERSION'
OPEN_ROSA_VERSION = '1.0'
DEFAULT_CONTENT_TYPE = 'text/xml; charset=utf-8'
NEW_OR_OLD_HOUSEHOLD_CHOICE_PATH = '//survey/chooseExistingHousehold'
HOUSEHOLD_SELECT_PATH = '//survey/registeredHousehold/household'
HOUSEHOLD_MEMBER_SELECT_PATH = '//survey/registeredHousehold/householdMember/h{{household_id}}'
HOUSEHOLD_MEMBER_ID_DELIMITER = '_'
MANUAL_HOUSEHOLD_SAMPLE_PATH = '//survey/household/houseNumber'
MANUAL_HOUSEHOLD_MEMBER_PATH = '//survey/household/householdMember'
ANSWER_PATH = '//survey/b{{batch_id}}/q{{question_id}}'
INSTANCE_ID_PATH = '//survey/meta/instanceID'
FORM_ID_PATH = '//survey/@id'
# ONLY_HOUSEHOLD_PATH = '//survey/onlyHousehold'
HOUSE_LISTING_FORM_ID_PREFIX = 'hreg_'
FORM_TYPE_PATH = '//survey/type'
HOUSE_NUMBER_PATH = '//survey/household/houseNumber'
HOUSEHOLD_PATH = '//survey/household'
PHYSICAL_ADDR_PATH = '//survey/household/physicalAddress'
HEAD_DESC_PATH = '//survey/household/headDesc'
HEAD_SEX_PATH = '//survey/household/headSex'
LISTING_COMPLETED = '//survey/listingCompleted'
MULTI_SELECT_XFORM_SEP = ' '
GEOPOINT_XFORM_SEP = ' '
# default content length for submission requests
DEFAULT_CONTENT_LENGTH = 10000000
MAX_DISPLAY_PER_COLLECTOR = 1000
LISTING = 'L'
SURVEY = 'S'
NON_RESPONSE = 'NR'
MALE = 'M'
FEMALE = 'F'
COULD_NOT_COMPLETE_SURVEY = '0'

LISTING_DESC = 'LISTING'
SURVEY_DESC = 'HOUSE MEMBER SURVEY'
NON_RESPONSE_DESC = 'NONE RESPONSE'

class NotEnoughHouseholds(ValueError):
    pass

class HouseholdNumberAlreadyExists(IntegrityError):
    pass

def _get_tree(xml_file):
    return etree.fromstring(xml_file.read())

def _get_nodes(search_path, tree=None, xml_string=None): #either tree or xml_string must be defined
    if tree is None:
        tree = etree.fromstring(xml_string)
    try:
        return tree.xpath(search_path)
    except Exception, ex:
        logger.error('Error retrieving path: %s, Desc: %s' % (search_path, str(ex)))

# def only_household_reg(survey_tree):
#     flag_nodes = _get_nodes(ONLY_HOUSEHOLD_PATH, tree=survey_tree)
#     return (flag_nodes is not None and len(flag_nodes) > 0 and flag_nodes[0].text == '1')
#
# def batches_included(survey_tree):
#     return only_household_reg(survey_tree) is False

def _get_household_members(survey_tree):
    member_nodes = _get_nodes(MANUAL_HOUSEHOLD_MEMBER_PATH, tree=survey_tree)
    return HouseholdMember.objects.filter(pk__in=[member_node.text for member_node in member_nodes]).all()

def _get_member_attrs(survey_tree):
    member_nodes = _get_nodes('%s/*' % MANUAL_HOUSEHOLD_MEMBER_PATH, tree=survey_tree)
    return dict([(member_node.tag, member_node.text) for member_node in member_nodes])

def _get_household_house_number(survey_tree):
    return _get_nodes(MANUAL_HOUSEHOLD_SAMPLE_PATH, tree=survey_tree)[0].text

def _get_household_physical_addr(survey_tree):
    return _get_nodes(PHYSICAL_ADDR_PATH, tree=survey_tree)[0].text

def _get_household_head_desc(survey_tree):
    return _get_nodes(HEAD_DESC_PATH, tree=survey_tree)[0].text

def _get_listing_completed(survey_tree):
    status = _get_nodes(LISTING_COMPLETED, tree=survey_tree)[0].text
    if status == '1': return True
    else: return False

def _get_household_head_sex(survey_tree):
    sex = _get_nodes(HEAD_SEX_PATH, tree=survey_tree)[0].text
    if sex == MALE:
        return True
    else:
        return False

def _choosed_existing_household(survey_tree):
    return _get_nodes(NEW_OR_OLD_HOUSEHOLD_CHOICE_PATH, tree=survey_tree)[0].text == '1'

def _get_selected_household_member(survey_tree):
    household_id = _get_nodes(HOUSEHOLD_SELECT_PATH, tree=survey_tree)[0].text
    context = template.Context({'household_id': household_id})
    hm_path = template.Template(HOUSEHOLD_MEMBER_SELECT_PATH).render(context)    
    member_id = (_get_nodes(hm_path, tree=survey_tree)[0].text).split(HOUSEHOLD_MEMBER_ID_DELIMITER)[1]
    return HouseholdMember.objects.get(pk=member_id)

def _get_or_create_household_member(interviewer, survey, survey_tree):
    house_number = _get_household_house_number(survey_tree)
    survey_listing = SurveyHouseholdListing.get_or_create_survey_listing(interviewer, survey)
    house_listing = survey_listing.listing
    try:
        household = Household.objects.get(listing=house_listing,
                                          house_number=house_number)
    except Household.DoesNotExist:
        physical_addr = ''
        try:
            physical_addr = _get_household_physical_addr(survey_tree)
        except IndexError:
            pass
        household = Household.objects.create(last_registrar=interviewer,
                                                listing=house_listing,
                                                registration_channel=ODKAccess.choice_name(),
                                                house_number=house_number, physical_address=physical_addr)
    #now time for member details
    MALE = '1'
    IS_HEAD = '1'
    mem_attrs = _get_member_attrs(survey_tree)
    kwargs = {}
    kwargs['surname'] = mem_attrs.get('surname')
    kwargs['first_name'] = mem_attrs['firstName']
    kwargs['gender'] = (mem_attrs['sex'] == MALE)
    date_of_birth = current_val = datetime.now() - relativedelta(years=int(mem_attrs['age']))
    kwargs['date_of_birth'] = date_of_birth
    #datetime.strptime(mem_attrs['dateOfBirth'], '%Y-%m-%d')
    kwargs['household'] = household
    kwargs['registrar'] = interviewer
    kwargs['registration_channel'] = ODKAccess.choice_name()
    kwargs['survey_listing'] = survey_listing
    if not household.get_head() and mem_attrs['isHead'] == IS_HEAD:
        # kwargs['occupation'] = mem_attrs.get('occupation', '')
        # kwargs['level_of_education'] = mem_attrs.get('levelOfEducation', '')
        # resident_since = datetime.strptime(mem_attrs.get('residentSince', '1900-01-01'), '%Y-%m-%d')
        # kwargs['resident_since']=resident_since
        head = HouseholdHead.objects.create(**kwargs)
        if household.head_desc is not head.surname:
            household.head_desc = head.surname
            household.save()
        return head
    else:
        return HouseholdMember.objects.create(**kwargs)

def record_interview_answer(interview, question, answer):
    if not isinstance(answer, NonResponseAnswer):
        answer_class = Answer.get_class(question.answer_type)
        print 'answer type ', answer_class.__name__
        print 'question is ', question
        print 'question pk is ', question.pk
        print 'interview is ', interview
        print 'answer text is ', answer
        return answer_class.create(interview, question, answer)
    else:
        answer.interview = interview
        answer.save()
        return answer

def _get_responses(interviewer, survey_tree, survey):
    response_dict = {}
    batches = interviewer.ea.open_batches(survey)
    for batch in batches:
        context = template.Context({'batch_id': batch.pk, })
        # non_response_path = template.Template(IS_NON_RESPONSE_PATH).render(context)
        # non_response_node = _get_nodes(non_response_path, tree=survey_tree)
        # if non_response_node and non_response_node[0].text.strip() == NON_RESPONSE:
        #     nrsp_answer_path = template.Template(NON_RESP_ANSWER_PATH).render(context)
        #     resp = NonResponseAnswer(batch.start_question, _get_nodes(nrsp_answer_path, tree=survey_tree)[0].text)
        #     response_dict[(batch.pk, batch.start_question.pk)] = resp
        # else:
        for question in batch.survey_questions:
            context['question_id'] = question.pk
            # context = template.Context({'batch_id': batch.pk, 'question_id' : question.pk})
            answer_path = template.Template(ANSWER_PATH).render(context)
            resp_text, resp_node = None, _get_nodes(answer_path, tree=survey_tree)
            if resp_node: #if question is relevant but
                resp_text = resp_node[0].text
            response_dict[(batch.pk, question.pk)] = resp_text
    return response_dict
                
def _get_instance_id(survey_tree):
    return _get_nodes(INSTANCE_ID_PATH, tree=survey_tree)[0].text

def _get_form_id(survey_tree):
    return _get_nodes(FORM_ID_PATH, tree=survey_tree)[0]

def _get_survey(survey_tree):
    pk = _get_nodes(FORM_ID_PATH, tree=survey_tree)[0]
    return Survey.objects.get(pk=pk)

def _get_form_type(survey_tree):
    return _get_nodes(FORM_TYPE_PATH, tree=survey_tree)[0].text

def save_household_list(interviewer, survey, survey_tree, survey_listing):
    house_nodes = _get_nodes(HOUSEHOLD_PATH, tree=survey_tree)
    if len(house_nodes) < survey.sample_size:
        raise NotEnoughHouseholds('Not enough households')
    house_number = 1
    households = []
    try:
        for node in house_nodes:
            household, _ = Household.objects.get_or_create(
                                    house_number=house_number,
                                     listing=survey_listing.listing,
                                     last_registrar=interviewer,
                                     registration_channel=ODKAccess.choice_name(),
                                     physical_address=_get_nodes('./physicalAddress', tree=node)[0].text,
                                     head_desc=_get_nodes('./headDesc', tree=node)[0].text,
                                     head_sex=_get_nodes('./headSex', tree=node)[0].text,
                        )
            house_number = house_number + 1
            households.append(household)
    except IntegrityError:
        raise HouseholdNumberAlreadyExists('Household number already exists')
    return households

def save_nonresponse_answers(interviewer, survey, survey_tree, survey_listing):
    house_nodes = _get_nodes(HOUSEHOLD_PATH, tree=survey_tree)
    house_number = 1
    non_responses = []
    for node in house_nodes:
        if _get_nodes('./nr', tree=node)[0].text == COULD_NOT_COMPLETE_SURVEY:
            nr_msg = _get_nodes('./qnsr', tree=node)[0].text if len(_get_nodes('./qnsr', tree=node)) \
                                                                else _get_nodes('./qnr', tree=node)[0].text
            non_responses.append(
                NonResponseAnswer.objects.create(
                    household=Household.objects.get(listing=survey_listing.listing,
                                                    house_number=_get_nodes('./houseNumber', tree=node)[0].text),
                    survey_listing=survey_listing,
                    interviewer=interviewer,
                    value=nr_msg
                )
            )
    return non_responses

@transaction.autocommit
def process_submission(interviewer, xml_file, media_files=[], request=None):
    """
    extract surveys and for this xml file and for specified household member
    """
    media_files = dict([(os.path.basename(f.name), f) for f in media_files])
    reports =  []
    survey_tree = _get_tree(xml_file)
    form_id = _get_form_id(survey_tree)
    survey = _get_survey(survey_tree)
    survey_allocation = get_survey_allocation(interviewer)
    household = None
    member = None
    survey_listing = SurveyHouseholdListing.get_or_create_survey_listing(interviewer, survey)
    if _get_form_type(survey_tree) == LISTING:
        households = save_household_list(interviewer, survey, survey_tree, survey_listing)
        survey_allocation.stage = SurveyAllocation.SURVEY
        survey_allocation.save()
        for household in households:
            submission = ODKSubmission.objects.create(interviewer=interviewer,
                    survey=survey, form_id= form_id, desc=LISTING_DESC,
                    instance_id=_get_instance_id(survey_tree), household_member=member, household=household,
                    xml=etree.tostring(survey_tree, pretty_print=True))
    elif _get_form_type(survey_tree) == NON_RESPONSE:
        non_responses = save_nonresponse_answers(interviewer, survey, survey_tree, survey_listing)
        for non_response in non_responses:
            submission = ODKSubmission.objects.create(interviewer=interviewer,
                    survey=survey, form_id= form_id, desc=NON_RESPONSE_DESC,
                    instance_id=_get_instance_id(survey_tree),
                    household_member=member, household=non_response.household,
                    xml=etree.tostring(survey_tree, pretty_print=True))
    else:
        member = _get_or_create_household_member(interviewer, survey, survey_tree)
        response_dict = _get_responses(interviewer, survey_tree, survey)
        treated_batches = {}
        interviews = {}
        if response_dict:
            for (b_id, q_id), answer in response_dict.items():
                question = Question.objects.get(pk=q_id)
                batch = treated_batches.get(b_id, Batch.objects.get(pk=b_id))
                if answer is not None:
                    if question.answer_type in [AudioAnswer.choice_name(), ImageAnswer.choice_name(), VideoAnswer.choice_name()]:
                        answer = media_files.get(answer, None)
                    interview = interviews.get(b_id, None)
                    if interview is None:
                        interview, _ = Interview.objects.get_or_create(
                                                   interviewer=interviewer,
                                                   householdmember=member,
                                                   batch=batch,
                                                   interview_channel=interviewer.odk_access[0],
                                                   ea=interviewer.ea
                                               )

                        interviews[b_id] = interview
                    created = record_interview_answer(interview, question, answer)
                if b_id not in treated_batches.keys():
                    treated_batches[b_id] = batch
            map(lambda batch: member.batch_completed(batch), treated_batches.values()) #create batch completion for question batches
            member.survey_completed()
            if member.household.has_completed(survey):
                map(lambda batch: member.household.batch_completed(batch, interviewer), treated_batches.values())
                member.household.survey_completed(survey, interviewer)
        household = member.household
        submission = ODKSubmission.objects.create(interviewer=interviewer,
                    survey=survey, form_id= form_id, desc=SURVEY_DESC,
                    instance_id=_get_instance_id(survey_tree), household_member=member, household=household,
                    xml=etree.tostring(survey_tree, pretty_print=True))
        #    execute.delay(submission.save_attachments, media_files)
        submission.save_attachments(media_files.values())
    return submission

def get_survey(interviewer):
    return SurveyAllocation.get_allocation(interviewer)

def get_survey_allocation(interviewer):
    return SurveyAllocation.get_allocation_details(interviewer)

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
            logger.debug('request meta: %s' % request.META['HTTP_AUTHORIZATION'])
            if authmeth.lower() == 'basic':
                auth = auth.strip().decode('base64')
                username, password = auth.split(':', 1)
                try:
                    request.user = ODKAccess.objects.get(user_identifier=username, odk_token=password, is_active=True).interviewer
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
        digestor = Digestor(method=request.method, path=request.get_full_path(), realm=realm)
        if request.META.has_key('HTTP_AUTHORIZATION'):
            logger.debug('request meta: %s' % request.META['HTTP_AUTHORIZATION'])
            try:
                parsed_header = digestor.parse_authorization_header(request.META['HTTP_AUTHORIZATION'])
                if parsed_header['realm'] == realm:
                    odk_access = ODKAccess.objects.get(user_identifier=parsed_header['username'], is_active=True)
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

