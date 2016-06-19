import csv
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.conf import settings
from survey.forms.filters import SurveyBatchFilterForm
from survey.forms.aggregates import InterviewerReportForm
from survey.models import Survey, Interviewer
from survey.models import Batch, LocationType, Household
from survey.services.results_download_service import ResultsDownloadService, ResultComposer
from survey.utils.views_helper import contains_key
from survey.forms.enumeration_area import LocationsFilterForm
from django.core.urlresolvers import reverse
from survey.utils.zip import InMemoryZip
from django_rq import job, get_scheduler
from rq import get_current_job
import json
from django.core.cache import cache
from channels import Group
from mics.routing import get_group_path


@job('email')
def send_mail(composer):
    composer.send_mail()

def safe_push_msg(user, msg):
    print 'request to send: ', msg
    #redis_key = settings.DOWNLOAD_CACHE_KEY%{'user_id':user.id, 'batch_id': batch_id}
    j = get_current_job()
    msg['ref_id'] = j.id
    # if cache.get(redis_key) is False: //to look at this later
    #     msg['expired'] = True #only add context id if entry still exists
    Group(get_group_path(user, settings.WEBSOCKET_URL)).send({'text': json.dumps(msg), })

@job('results-queue')
def generate_result_link(current_user, download_service, file_name):
    scheduler = get_scheduler('ws-notice')
    batch_id = download_service.batch.id
    redis_key = settings.DOWNLOAD_CACHE_KEY%{'user_id':current_user.id, 'batch_id': batch_id}
    repeat_times = settings.DOWNLOAD_CACHE_DURATION/settings.UPDATE_INTERVAL
    if cache.has_key(redis_key) is False:
        scheduled_job = scheduler.schedule(datetime.utcnow(), safe_push_msg,
                                    args=[current_user, {'msg_type' : 'notice',
                                                         'content': 'Computing results...',
                                                          'status': 'WIP',
                                                         'context': 'download-data',
                                                          'context_id' : batch_id,
                                                         'description': download_service.batch.name
                                                          }],
                                    interval=settings.UPDATE_INTERVAL,
                                    repeat=repeat_times, #keep sending this update until 30mins
                                    result_ttl=settings.DOWNLOAD_CACHE_DURATION)
        data = download_service.generate_interview_reports()
        #when you are done extracting, cancel job
        scheduled_job.cancel()
        #now save the cache the result in redis
        cache.set(redis_key, {'filename': file_name, 'data': data}, settings.DOWNLOAD_CACHE_DURATION)
    #keep notifying for download link, probably until it's downloaded
    scheduled_job = scheduler.schedule(datetime.utcnow(), safe_push_msg,
                                args=[current_user, {
                                'msg_type' : 'notice',
                                'content': reverse('download_export_results', args=(batch_id, )),
                                'context_id' : batch_id,
                                'status': 'DONE',
                                'context': 'download-data',
                                'description': download_service.batch.name
                                 }],
                                interval=settings.UPDATE_INTERVAL,
                                repeat=repeat_times, #keep sending this update until 30mins
                                result_ttl=settings.DOWNLOAD_CACHE_DURATION)

@login_required
@permission_required('auth.can_view_aggregates')
def download_results(request, batch_id):
    redis_key = settings.DOWNLOAD_CACHE_KEY%{'user_id':request.user.id, 'batch_id' : batch_id}
    download = cache.get(redis_key)
    if download:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % download['filename']
        writer = csv.writer(response)
        data = download['data']
        contents = data[0]
        for row in data[1:]:
            writer.writerow(row)
        return response
    else:
        return HttpResponseNotFound()


@login_required
@permission_required('auth.can_view_aggregates')
def download(request):
    survey_batch_filter_form = SurveyBatchFilterForm(data=request.GET)
    locations_filter = LocationsFilterForm(data=request.GET)
    last_selected_loc = locations_filter.last_location_selected
    if request.GET and request.GET.get('action'):
        survey_batch_filter_form = SurveyBatchFilterForm(data=request.GET)
        if survey_batch_filter_form.is_valid():
            batch = survey_batch_filter_form.cleaned_data['batch']
            survey = survey_batch_filter_form.cleaned_data['survey']
            multi_option = survey_batch_filter_form.cleaned_data['multi_option']
            restricted_to = None
            if last_selected_loc:
                restricted_to = [last_selected_loc, ]
            if request.GET.get('action') == 'Email Spreadsheet':
                composer = ResultComposer(request.user,
                                          ResultsDownloadService(batch=batch,
                                                                 survey=survey,
                                                                 restrict_to=restricted_to,
                                                                multi_display=multi_option))
                send_mail.delay(composer)
                messages.warning(request, "Email would be sent to you shortly. This could take a while.")
            else:
                download_service = ResultsDownloadService(batch=batch, survey=survey, restrict_to=restricted_to,
                                  multi_display=multi_option)
                file_name = '%s%s' % ('%s-%s-'% (last_selected_loc.type.name, last_selected_loc.name) if
                                      last_selected_loc else '', batch.name if batch else survey.name)
                generate_result_link.delay(request.user, download_service, file_name)
                messages.warning(request, "Download is in progress...")
    loc_types = LocationType.in_between()
    return render(request, 'aggregates/download_excel.html',
                  {
                      'survey_batch_filter_form': survey_batch_filter_form,
                      'locations_filter' : locations_filter,
                      'export_url' : '%s?%s' % (reverse('excel_report'), request.META['QUERY_STRING']),
                      'location_filter_types' : loc_types
                  })

@login_required
@permission_required('auth.can_view_aggregates')
def _list(request):
    surveys = Survey.objects.order_by('name')
    batches = Batch.objects.order_by('order')
    return render(request, 'aggregates/download_excel.html', {'batches': batches, 'surveys': surveys})

@login_required
@permission_required('auth.can_view_aggregates')
def completed_interviewer(request):
    batch = None
    survey = None
    params = request.POST or request.GET
    if contains_key(params, 'survey'):
        survey = Survey.objects.get(id=params['survey'])
    if contains_key(params, 'batch'):
        batch = Batch.objects.get(id=params['batch'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="interviewer.csv"'
    header = ['Interviewer', 'Access Channels']
    header.extend(LocationType.objects.exclude(name__iexact='country').values_list('name', flat=True))
    data = [header]
    data.extend(survey.generate_completion_report(batch=batch))
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    return response

@permission_required('auth.can_view_aggregates')
def interviewer_report(request):
    if request.GET and request.GET.get('action'):
        return completed_interviewer(request)
    report_form = InterviewerReportForm(request.GET)
    return render(request, 'aggregates/download_interviewer.html', {'report_form': report_form, })
