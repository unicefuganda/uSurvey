from datetime import datetime
import pytz, os, base64, random, logging
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
from survey.odk.utils.odk_helper import get_survey, process_submission, disposition_ext_and_date, get_zipped_dir, \
    response_with_mimetype_and_name, OpenRosaResponseBadRequest, OpenRosaRequestForbidden, \
    OpenRosaResponseNotAllowed, OpenRosaResponse, OpenRosaResponseNotFound, OpenRosaServerError, \
    BaseOpenRosaResponse, HttpResponseNotAuthorized, http_digest_interviewer_auth
from survey.models import Survey, Interviewer, Household, ODKSubmission, Answer, Batch
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from survey.utils.query_helper import get_filterset
from survey.models.surveys import SurveySampleSizeReached
from survey.interviewer_configs import LEVEL_OF_EDUCATION, NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER
from survey.interviewer_configs import MESSAGES


def get_survey_xform(interviewer, batch):
    selectable_households = None
    household_size = interviewer.ea.total_households
    if interviewer.may_commence(batch.survey):
        registered_households = interviewer.generate_survey_households(batch.survey)
        return render_to_string("odk/survey_form_without_house_reg.xml", {
            'interviewer': interviewer,
            'registered_households': registered_households, #interviewer.households.filter(survey=survey, ea=interviewer.ea).all(),
            'title' : '%s - %s' % (batch.survey, batch),
            'survey' : batch.survey,
            'survey_batches' : [batch, ],
            'educational_levels' : LEVEL_OF_EDUCATION,
            'answer_types' : dict([(cls.__name__.lower(), cls.choice_name()) for cls in Answer.supported_answers()])
            })
    else:
        selectable_households = range(1, household_size + 1)
        return render_to_string("odk/household_registration.xml", {
            'interviewer': interviewer,
            'survey' : batch.survey,
            'educational_levels' : LEVEL_OF_EDUCATION,
            'selectable_households' : selectable_households,
            'messages' : MESSAGES,
            })

@login_required
@permission_required('auth.can_view_aggregates')
def download_submission_attachment(request, submission_id):
    odk_submission = ODKSubmission.objects.get(pk=submission_id)
    filename = '%s-%s-%s.zip' % (odk_submission.survey.name, odk_submission.household_member.pk, odk_submission.interviewer.pk)
    attachment_dir = os.path.join(settings.SUBMISSION_UPLOAD_BASE, str(odk_submission.pk), 'attachments')
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    response.write(get_zipped_dir(attachment_dir))
    return response


@login_required
@permission_required('auth.can_view_aggregates')
def submission_list(request):
    odk_submissions = ODKSubmission.objects.all()
    search_fields = ['interviewer__name', 'interviewer__ea__name', 'survey__name', 'household_member__household__uid', 'form_id', 'instance_id']
    if request.GET.has_key('q'):
        odk_submissions = get_filterset(odk_submissions, request.GET['q'], search_fields)
    return render(request, 'odk/submission_list.html', { 'submissions' : odk_submissions,
                                                 'request': request})

@http_digest_interviewer_auth
@require_GET
def form_list(request):
    """
        This is where ODK Collect gets its download list.
    """
    interviewer = request.user
    household_size = interviewer.ea.total_households
    #get_object_or_404(Interviewer, mobile_number=username, odk_token=token)
    #to do - Make fetching households more e
    survey = get_survey(interviewer)
    audit = {}
    audit_log(Actions.USER_FORMLIST_REQUESTED, request.user, interviewer,
          _("Requested forms list. for %s" % interviewer.name), audit, request)
    content = render_to_string("odk/xformsList.xml", {
    'batches': interviewer.ea.open_batches(survey),
    'interviewer' : interviewer,
    'request' : request,
    'household_size' : household_size
    })
    response = BaseOpenRosaResponse(content)
    response.status_code = 200
    return response

@http_digest_interviewer_auth
def download_xform(request, batch_id):
    interviewer = request.user
    batch = get_object_or_404(Batch, pk=batch_id)
    survey_xform = get_survey_xform(interviewer, batch)
    form_id = '%s'% batch_id
    audit = {
        "xform": form_id
    }
    audit_log( Actions.FORM_XML_DOWNLOADED, request.user, interviewer, 
                _("Downloaded XML for form '%(id_string)s'.") % {
                                                        "id_string": form_id
                                                    }, audit, request)
    response = response_with_mimetype_and_name('xml', 'survey-%s' %batch_id,
                                               show_date=False, full_mime='text/xml')
    response.content = survey_xform
    return response

@http_digest_interviewer_auth
@require_http_methods(["POST"])
@csrf_exempt
def submission(request):
    interviewer = request.user
    #get_object_or_404(Interviewer, mobile_number=username, odk_token=token)
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
        submission_report = process_submission(interviewer, xml_file_list[0],             media_files=media_files)
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
        audit_log( Actions.SUBMISSION_CREATED, request.user, interviewer, 
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
        audit_log( Actions.SUBMISSION_REQUESTED, request.user, interviewer, 
            _("Failed attempted to submit XML for form for interviewer: '%(interviewer)s'. desc: '%(desc)s'") % {
                                                        "interviewer": interviewer.name,
                                                        "desc" : str(ex)
                                                    }, {'desc' : str(ex)}, request, logging.WARNING)
        return OpenRosaServerError(u"An error occurred. Please try again")

