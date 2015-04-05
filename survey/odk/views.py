from datetime import datetime
import pytz, os, base64, random
from functools import wraps
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404, render
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect, HttpResponseForbidden, Http404, StreamingHttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.files.storage import get_storage_class
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.template import RequestContext, loader, Context
from survey.odk.utils.log import audit_log, Actions, logger
from survey.odk.utils.odk_helper import get_surveys, process_submission, disposition_ext_and_date, get_zipped_dir, \
    response_with_mimetype_and_name, OpenRosaResponseBadRequest, OpenRosaRequestForbidden, \
    OpenRosaResponseNotAllowed, OpenRosaResponse, OpenRosaResponseNotFound, OpenRosaServerError, \
    BaseOpenRosaResponse, HttpResponseNotAuthorized, http_digest_investigator_auth
from survey.models import Survey, Investigator, Household
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from survey.utils.query_helper import get_filterset
from survey.models import ODKSubmission
from survey.models.surveys import SurveySampleSizeReached
from survey.investigator_configs import LEVEL_OF_EDUCATION, NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR

def get_survey_xform(investigator, survey, household_size):
    selectable_households = None
    if household_size:
        household_size = int(household_size)
        if survey.has_sampling:
            selectable_households = random.sample(list(range(1, household_size + 1)), NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR)
            selectable_households.sort()
        else:
            selectable_households = range(1, household_size + 1)
    registered_households = [hhd for hhd in investigator.households.filter(survey=survey, ea=investigator.ea).all() if hhd.all_members()]
    return render_to_string("odk/survey_form.xml", {
        'investigator': investigator,
        'registered_households' : registered_households, #investigator.households.filter(survey=survey, ea=investigator.ea).all(),
        'survey' : survey,
        'survey_batches' : investigator.get_open_batch_for_survey(survey, sort=True),
        'educational_levels' : LEVEL_OF_EDUCATION,
        'selectable_households' : selectable_households
        })

def base_url(request):
    return '%s://%s' % (request.META.get('wsgi.url_scheme'), request.META.get('HTTP_HOST')) #Site.objects.get_current().name;

@login_required
@permission_required('auth.can_view_aggregates')
def download_submission_attachment(request, submission_id):
    odk_submission = ODKSubmission.objects.get(pk=submission_id)
    filename = '%s-%s-%s.zip' % (odk_submission.survey.name, odk_submission.household_member.pk, odk_submission.investigator.pk)
    attachment_dir = os.path.join(settings.SUBMISSION_UPLOAD_BASE, str(odk_submission.pk), 'attachments')
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    response.write(get_zipped_dir(attachment_dir))
    return response


@login_required
@permission_required('auth.can_view_aggregates')
def submission_list(request):
    odk_submissions = ODKSubmission.objects.all()
    search_fields = ['investigator__name', 'survey__name', 'household__uid', 'form_id', 'instance_id']
    if request.GET.has_key('q'):
        odk_submissions = get_filterset(odk_submissions, request.GET['q'], search_fields)
    return render(request, 'odk/submission_list.html', { 'submissions' : odk_submissions,
                                                 'request': request})

@http_digest_investigator_auth
@require_GET
def form_list(request):
    """
        This is where ODK Collect gets its download list.
    """
    investigator = request.user
    household_size = request.GET.get('total_households_ea', '')
    #get_object_or_404(Investigator, mobile_number=username, odk_token=token)
    #to do - Make fetching households more e
    surveys = get_surveys(investigator)
    audit = {}
    audit_log(Actions.USER_FORMLIST_REQUESTED, request.user, investigator,
          _("Requested forms list. for %s" % investigator.mobile_number), audit, request)
    context= Context({
    'surveys': surveys,
    'investigator' : investigator,
    'base_url' : base_url(request),
    'household_size' : household_size
    })
    t = loader.get_template("odk/xformsList.xml")
    response = BaseOpenRosaResponse(t.render(context))
    response.status_code = 200
    return response

@http_digest_investigator_auth
def download_xform(request, survey_id, household_size=None):
    investigator = request.user
    survey = get_object_or_404(Survey, pk=survey_id)
    survey_xform = get_survey_xform(investigator, survey, household_size)
    form_id = '%s'% survey_id
    audit = {
        "xform": form_id
    }
    audit_log( Actions.FORM_XML_DOWNLOADED, request.user, investigator, 
                _("Downloaded XML for form '%(id_string)s'.") % {
                                                        "id_string": form_id
                                                    }, audit, request)
    response = response_with_mimetype_and_name('xml', 'survey%s' %survey_id,
                                               show_date=False, full_mime='text/xml')
    response.content = survey_xform
    return response

@http_digest_investigator_auth
@require_http_methods(["POST"])
@csrf_exempt
def submission(request):
    investigator = request.user
    #get_object_or_404(Investigator, mobile_number=username, odk_token=token)
    submission_date = datetime.now().isoformat()
    xml_file_list = []
    html_response = False
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    try:
        xml_file_list = request.FILES.pop("xml_submission_file", [])
        if len(xml_file_list) != 1:
            return OpenRosaResponseBadRequest(u"There should be a single XML submission file.")
        media_files = request.FILES.values()
        submission_report = process_submission(investigator, xml_file_list[0],             media_files=media_files)
        logger.info(submission_report)
        context = Context({
        'message' : settings.ODK_SUBMISSION_SUCCESS_MSG,
        'instanceID' : u'uuid:%s' % submission_report.instance_id,
        'formid' : submission_report.form_id,
        'submissionDate' : submission_date,
        'markedAsCompleteDate' : submission_date
        })
        t = loader.get_template('odk/submission.xml')
        audit = {}
        audit_log( Actions.SUBMISSION_CREATED, request.user, investigator, 
            _("Submitted XML for form '%(id_string)s'.") % {
                                                        "id_string": submission_report.form_id
                                                    }, audit, request)
        response = BaseOpenRosaResponse(t.render(context))
        response.status_code = 201
        response['Location'] = request.build_absolute_uri(request.path)
        return response
    except SurveySampleSizeReached:
        return OpenRosaRequestForbidden(u"Max sample size reached for this survey")
    except Exception, ex:
        audit_log( Actions.SUBMISSION_REQUESTED, request.user, investigator, 
            _("Failed attempted to submit XML for form for investigator: '%(investigator)s'. desc: '%(desc)s'") % {
                                                        "investigator": investigator.mobile_number,
                                                        "desc" : str(ex)
                                                    }, {'desc' : str(ex)}, request, logging.WARNING)
        return OpenRosaServerError(u"Unexpected error while processing your form. Please try again")

