from django.shortcuts import render
from django.http import HttpResponse
from survey.models import Batch
import csv

def download(request):
    batch = Batch.objects.get(id = request.POST['batch'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % batch.name
    data = batch.generate_report()
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    return response

def list(request):
    batches = Batch.objects.order_by('order').all()
    return render(request, 'aggregates/download_excel.html', {'batches': batches})