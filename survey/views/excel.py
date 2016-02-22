import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from survey.forms.filters import SurveyBatchFilterForm
from survey.forms.aggregates import InterviewerReportForm
from survey.models import Survey, Interviewer
from survey.models import Batch, LocationType, Household
from survey.services.results_download_service import ResultsDownloadService, ResultComposer
from survey.utils.views_helper import contains_key
from survey.tasks import email_task
from survey.forms.enumeration_area import LocationsFilterForm
from django.core.urlresolvers import reverse
from survey.utils.zip import InMemoryZip
from django_rq import job


def _process_export(survey_batch_filter_form, last_selected_loc):
    batch = survey_batch_filter_form.cleaned_data['batch']
    survey = survey_batch_filter_form.cleaned_data['survey']
    restrict_to = None
    multi_option = survey_batch_filter_form.cleaned_data['multi_option']
    response = HttpResponse(content_type='text/csv')
    file_name = '%s%s' % ('%s-%s-'% (last_selected_loc.type.name, last_selected_loc.name) if last_selected_loc else '',
                          batch.name if batch else survey.name)
    if last_selected_loc:
        restrict_to = [last_selected_loc, ]
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % file_name
    data = ResultsDownloadService(batch=batch, survey=survey, restrict_to=restrict_to,
                                  multi_display=multi_option).generate_interview_reports()
    # writer = csv.writer(response)
    zipf = InMemoryZip()
    contents = data[0]
    for row in data[1:]:
        contents = '%s\n%s' % (contents, row)
        #writer.writerow(row)

    return response

@job('email')
def send_mail(composer):
    composer.send_mail()

@login_required
@permission_required('auth.can_view_aggregates')
def download(request):
    survey_batch_filter_form = SurveyBatchFilterForm(data=request.GET)
    locations_filter = LocationsFilterForm(data=request.GET)
    last_selected_loc = locations_filter.last_location_selected
    if request.GET and request.GET.get('action'):
        survey_batch_filter_form = SurveyBatchFilterForm(data=request.GET)
        if survey_batch_filter_form.is_valid():
            if request.GET.get('action') == 'Email Spreadsheet':
                batch = survey_batch_filter_form.cleaned_data['batch']
                survey = survey_batch_filter_form.cleaned_data['survey']
                multi_option = survey_batch_filter_form.cleaned_data['multi_option']
                composer = ResultComposer(request.user,
                                          ResultsDownloadService(batch=batch,
                                                                 survey=survey,
                                                                 restrict_to=[last_selected_loc, ],
                                                                multi_display=multi_option))
                send_mail.delay(composer)
                messages.warning(request, "Email would be sent to you shortly. This could take a while.")
            else:
                return _process_export(survey_batch_filter_form, last_selected_loc)
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
