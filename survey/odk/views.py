from datetime import datetime
import pytz
import os
import base64
import random
import logging
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
from .utils.log import audit_log, Actions, logger
from .utils.odk_helper import (
    get_survey_allocation,
    process_submission,
    disposition_ext_and_date,
    get_zipped_dir,
    response_with_mimetype_and_name,
    OpenRosaResponseBadRequest,
    OpenRosaRequestForbidden,
    OpenRosaRequestConflict,
    OpenRosaResponseNotAllowed,
    OpenRosaResponse,
    OpenRosaResponseNotFound,
    OpenRosaServerError,
    BaseOpenRosaResponse,
    HttpResponseNotAuthorized,
    http_digest_interviewer_auth,
    NotEnoughData)
from survey.models import (
    Survey,
    Interviewer,
    ODKSubmission,
    Answer,
    Batch,
    SurveyAllocation,
    ODKFileDownload,
    Interview,
    QuestionSet)
from survey.models import ListingSample
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from survey.utils.query_helper import get_filterset
from survey.models import BatchLocationStatus
from collections import OrderedDict


def get_qset_xform(interviewer, allocations, qset, ea_samples={}):
    return render_to_string("odk/question_set.xml",
                            {'interviewer': interviewer,
                             'qset': qset,
                             'stage': allocations[0].stage,
                                'assignments': allocations,
                                'non_response_reasons': settings.NON_RESPONSE_REASONS,
                                'answer_types': dict([(
                                    cls.__name__.lower(),
                                    cls.choice_name())
                                    for cls in Answer.supported_answers()]),
                                'ea_samples': ea_samples,
                             })


@login_required
@permission_required('auth.can_view_aggregates')
def download_submission_attachment(request, submission_id):
    odk_submission = ODKSubmission.objects.get(pk=submission_id)
    filename = '%s-%s-%s.zip' % (odk_submission.survey.name,
                                 odk_submission.household_member.pk,
                                 odk_submission.interviewer.pk)
    attachment_dir = os.path.join(
        settings.SUBMISSION_UPLOAD_BASE, str(odk_submission.pk), 'attachments')
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    response.write(get_zipped_dir(attachment_dir))
    return response


@login_required
@permission_required('auth.can_view_aggregates')
def submission_list(request):
    odk_submissions = ODKSubmission.objects.all().order_by('-created')
    search_fields = [
        'interviewer__name',
        'interviewer__ea__name',
        'survey__name',
        'form_id',
        'instance_id']
    if 'q' in request.GET:
        odk_submissions = get_filterset(
            odk_submissions, request.GET['q'], search_fields)
    return render(request,
                  'odk/submission_list.html',
                  {'submissions': odk_submissions,
                   'placeholder': 'interviewer, house, member, survey',
                   'request': request})


@http_digest_interviewer_auth
@require_GET
def instances_form_list(request):
    """ This is where ODK Collect gets its download list.
    Get all ODK submissions for this EA and survey
    """
    interviewer = request.user
    assignments = interviewer.unfinished_assignments
    submissions = ODKSubmission.objects.filter(status=ODKSubmission.COMPLETED,
                                               ea__in=[a.allocation_ea for a in assignments],
                                               survey=assignments.first().survey)  # pick irrespective of status
    # now exclude any question already being used as a sample sample
    listing_interviews = ListingSample.objects.values_list(
        'interview', flat=True)
    submissions = submissions.exclude(interviews__in=listing_interviews)
    content = render_to_string("odk/instances_xformsList.xml", {
        'interviewer': interviewer,
        'submissions': submissions,
        'request': request,
    })
    response = BaseOpenRosaResponse(content)
    response.status_code = 200
    return response


@http_digest_interviewer_auth
def download_odk_submissions(request, submission_id):
    interviewer = request.user
    submission = get_object_or_404(ODKSubmission,
        # check if the interviewer authorized for this submission EA!
        pk=submission_id,
        ea__in=[a.allocation_ea for a in interviewer.unfinished_assignments],
    )
    response = BaseOpenRosaResponse(submission.xml)
    response.status_code = 200
    return response


@http_digest_interviewer_auth
@require_GET
def form_list(request):
    """ This is where ODK Collect gets its download list.
    """
    interviewer = request.user
    #get_object_or_404(Interviewer, mobile_number=username, odk_token=token)
    # to do - Make fetching households more e
    assignments = get_survey_allocation(interviewer)
    if assignments.count():
        # now removed the condition for open batches
        # this is done in favor of doing the computation later when needed.
        # by design an interviewer is only
        survey = assignments[0].survey
        # assigned to perform same survey in different eas
        audit_log(
            Actions.USER_FORMLIST_REQUESTED, request.user, interviewer, _(
                "survey allocation %s: %s" %
                (interviewer, survey)), {}, request)
        audit = {}
        audit_log(
            Actions.USER_FORMLIST_REQUESTED, request.user, interviewer, _(
                "Requested forms list. for alloc: %s:%s" %
                (survey, interviewer)), audit, request)
        open_batches = set()
        for assignment in assignments:
            open_batches.update(assignment.allocation_ea.open_batches(survey))
        content = render_to_string("odk/xformsList.xml", {
            'assignments': assignments,
            'survey': survey,
            'interviewer': interviewer,
            'request': request,
            'Const': SurveyAllocation,
            'open_batches': open_batches
        })
        response = BaseOpenRosaResponse(content)
        response.status_code = 200
        return response
    else:
        return OpenRosaResponseNotFound('No survey allocated presently')


@http_digest_interviewer_auth
def download_xform(request, batch_id):
    interviewer = request.user
    batch = get_object_or_404(Batch, pk=batch_id)
    survey = batch.survey
    ea_samples = {}
    assignments = get_survey_allocation(interviewer)
    if assignments and survey.has_sampling:
        assignments.update(stage=SurveyAllocation.SURVEY)
        for assignment in assignments:
            if assignment.sample_size_reached(
            ):            # only randomize eas that has reached sample size
                ea = assignment.allocation_ea
                listing_survey = survey.preferred_listing or survey
                try:
                    ListingSample.generate_random_samples(
                        listing_survey, survey, ea)
                except ListingSample.SamplesAlreadyGenerated:
                    pass
                ea_samples[ea.pk] = ListingSample.samples(survey, ea)
    return _get_qset_response(
        request,
        interviewer,
        assignments,
        batch,
        ea_samples=ea_samples)


@http_digest_interviewer_auth
def download_listing_xform(request):
    interviewer = request.user
    assignments = get_survey_allocation(interviewer)
    qset = assignments[0].survey.listing_form
    response = OpenRosaResponseNotFound('No survey allocated')
    return _get_qset_response(request, interviewer, assignments, qset)


def _get_qset_response(request, interviewer, assignments, qset, ea_samples={}):
    response = OpenRosaResponseNotFound('No survey allocated')
    if assignments.count():
        # all assignemnts are of same survey
        survey = assignments[0].survey
        download = ODKFileDownload.objects.create()
        # record file downloads for all eas of this inviewer
        map(
            lambda assignment: download.assignments.add(assignment),
            assignments)
        qset_xform = get_qset_xform(
            interviewer, assignments, qset, ea_samples=ea_samples)
        form_id = 'allocation-%s-%s' % (survey.id, interviewer.id)
        audit = {
            "xform": form_id
        }
        audit_log(
            Actions.FORM_XML_DOWNLOADED,
            request.user,
            interviewer,
            _("'%(interviewer)s' Downloaded XML for form '%(id_string)s'.") % {
                "interviewer": interviewer.name,
                "id_string": form_id},
            audit,
            request)
        response = response_with_mimetype_and_name('xml', '-'.join([qset.verbose_name(), str(survey.pk)]),
                                                   show_date=False, full_mime='text/xml')
        response.content = qset_xform
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
            return OpenRosaResponseBadRequest(
                u"There should be a single XML submission file.")
        media_files = request.FILES
        submission_report = process_submission(interviewer, xml_file_list[0], media_files=media_files)
        logger.info(submission_report)
        context = Context({
            'message': settings.ODK_SUBMISSION_SUCCESS_MSG,
            'instanceID': u'uuid:%s' % submission_report.instance_id,
            'formid': submission_report.form_id,
            'submissionDate': submission_date,
            'markedAsCompleteDate': submission_date
        })
        t = loader.get_template('odk/submission.xml')
        audit = {}
        audit_log(
            Actions.SUBMISSION_CREATED,
            request.user,
            interviewer,
            _("'%(interviewer)s' Submitted XML for form \
                '%(id_string)s'. Desc: '%(desc)s'") % {
                "interviewer": interviewer.name,
                "desc": submission_report.description,
                "id_string": submission_report.form_id},
            audit,
            request)
        response = BaseOpenRosaResponse(t.render(context))
        response.status_code = 201
        response['Location'] = request.build_absolute_uri(request.path)
        return response
    except NotEnoughData:
        desc = settings.ODK_UPLOADED_DATA_BELOW_SAMPLE_SIZE
        audit_log(Actions.SUBMISSION_REQUESTED, request.user, interviewer,
                  _("Failed attempted to submit XML for form for interviewer: \
                    '%(interviewer)s'. desc: '%(desc)s'") % {
                      "interviewer": interviewer.name,
                      "desc": desc
                  }, {'desc': desc}, request, logging.WARNING)
        return OpenRosaRequestForbidden(desc)
    except ValueError as err:
        desc = str(err)
        audit_log(Actions.SUBMISSION_REQUESTED, request.user, interviewer,
                  _("Failed attempted to submit XML for form for interviewer: \
                        '%(interviewer)s'. desc: '%(desc)s'") % {
                      "interviewer": interviewer.name,
                      "desc": desc
                  }, {'desc': desc}, request, logging.WARNING)
        return OpenRosaRequestForbidden(desc)
    except Exception as ex:
        audit_log(Actions.SUBMISSION_REQUESTED, request.user, interviewer,
                  _("Failed attempted to submit XML for form for interviewer:\
                        '%(interviewer)s'. desc: '%(desc)s'") % {
                      "interviewer": interviewer.name,
                      "desc": str(ex)
                  }, {'desc': str(ex)}, request, logging.WARNING)
        return OpenRosaServerError(settings.ODK_ERROR_OCCURED)
