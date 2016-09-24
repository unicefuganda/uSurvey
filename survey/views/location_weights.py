from datetime import datetime
from dateutil.parser import parse
from django.utils.timezone import utc
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from survey.models import LocationType, Location
from survey.forms.upload_csv_file import UploadWeightsForm
from survey.models import LocationWeight, LocationTypeDetails, UploadErrorLog, Survey
from survey.forms.enumeration_area import LocationsFilterForm
from survey.views.location_widget import LocationWidget
from survey.utils.views_helper import contains_key
from django.core.urlresolvers import reverse
from django_rq import job


@job('default')
def begin_upload(upload_form):
    upload_form.upload()


@job('upload_task')
def uploadtask(composer):
    composer.uploadtask()


@permission_required('auth.can_view_batches')
def upload(request):
    upload_form = UploadWeightsForm()
    if request.method == 'POST':
        upload_form = UploadWeightsForm(request.POST, request.FILES)
        if upload_form.is_valid():
            begin_upload.delay(upload_form)
            messages.warning(
                request, "Upload in progress. This could take a while.")
            return HttpResponseRedirect('/locations/weights/upload/')

    context = {'button_label': 'Upload', 'id': 'upload-location-weights-form',
               'upload_form': upload_form, 'location_types': LocationType.objects.all(), 'range': range(3)}

    return render(request, 'locations/weights/upload.html', context)


@login_required
@permission_required('auth.can_view_batches')
def list_weights(request):
    location_weights = LocationWeight.objects.all()
    surveys = Survey.objects.all()
    survey = None
    selected_location = None
    params = request.GET or request.POST
    location_filter_form = LocationsFilterForm(data=params)
    if contains_key(params, 'survey'):
        survey = Survey.objects.get(id=params['survey'])
        location_weights = location_weights.filter(survey=survey)
    if location_filter_form.last_location_selected:
        location_weights = location_weights.filter(
            location=location_filter_form.last_location_selected)

    location_types = LocationType.objects.exclude(name__iexact="country")
    context = {'location_weights': location_weights,
               'location_types': location_types,
               'locations_filter': location_filter_form,
               'surveys': surveys,
               'selected_survey': survey,
               'action': reverse('list_weights_page'),
               'request': request}
    return render(request, 'locations/weights/index.html', context)


@permission_required('auth.can_view_batches')
def error_logs(request):
    location_weights_error_logs = UploadErrorLog.objects.filter(
        model='WEIGHTS')
    today = datetime.now().replace(tzinfo=utc).strftime('%Y-%m-%d')
    selected_from_date = today
    selected_to_date = today
    params = request.GET
    if params.get('from_date', None) and params.get('to_date', None):
        selected_from_date = parse(
            params['from_date'], dayfirst=False, fuzzy=True).replace(tzinfo=utc)
        selected_to_date = parse(
            params['to_date'], dayfirst=False, fuzzy=True).replace(tzinfo=utc)

        location_weights_error_logs = location_weights_error_logs.filter(created__range=[selected_from_date,
                                                                                         selected_to_date])

    context = {'error_logs': location_weights_error_logs, 'request': request,
               'selected_from_date': selected_from_date, 'selected_to_date': selected_to_date}

    return render(request, 'locations/weights/error_logs.html', context)
