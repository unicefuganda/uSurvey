import csv

from django.shortcuts import render

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required, permission_required
from survey.forms.filters import IndicatorFilterForm
from survey.models import Survey, Investigator
from survey.models.batch import Batch
from survey.services.results_download_service import ResultsDownloadService
from survey.views.views_helper import contains_key


@login_required
@permission_required('auth.can_view_aggregates')
def download(request):
    batch = Batch.objects.get(id=request.POST['batch'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % batch.name
    data = ResultsDownloadService(batch).generate_report()
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    return response

@login_required
@permission_required('auth.can_view_aggregates')
def _list(request):
    surveys = Survey.objects.order_by('name')
    batches = Batch.objects.order_by('order')
    return render(request, 'aggregates/download_excel.html', {'batches': batches, 'surveys': surveys})

@login_required
@permission_required('auth.can_view_aggregates')
def completed_investigator(request):
    batch = None
    survey = None
    params = request.POST
    if contains_key(params, 'survey'):
        survey = Survey.objects.get(id=params['survey'])
    if contains_key(params, 'batch'):
        batch = Batch.objects.get(id=params['batch'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="investigator.csv"'
    data = Investigator.generate_completion_report(survey, batch=batch)
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    return response

@permission_required('auth.can_view_aggregates')
def investigator_report(request):
    surveys = Survey.objects.all()
    batches = Batch.objects.all()
    return render(request, 'aggregates/download_investigator.html', {'surveys':surveys, 'batches': batches})