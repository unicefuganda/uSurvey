import csv

from django.shortcuts import render

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required, permission_required
from survey.models import Survey
from survey.models.batch import Batch
from survey.models.investigator import Investigator


@login_required
@permission_required('auth.can_view_aggregates')
def download(request):
    batch = Batch.objects.get(id = request.POST['batch'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % batch.name
    data = batch.generate_report(Investigator)
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    return response

@login_required
@permission_required('auth.can_view_aggregates')
def list(request):
    batches = Batch.objects.order_by('order').all()
    return render(request, 'aggregates/download_excel.html', {'batches': batches})

def completed_investigator(request):
    survey = Survey.objects.get(id = request.POST['survey'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="investigator.csv"'
    data = Investigator.genrate_completion_report(survey)
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    return response