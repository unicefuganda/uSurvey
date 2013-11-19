from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required

from django.http import HttpResponseRedirect
from django.shortcuts import render
from rapidsms.contrib.locations.models import LocationType, Location

from survey.forms.upload_csv_file import UploadWeightsForm
from survey.models import LocationWeight, LocationTypeDetails, UploadErrorLog, Survey
from survey.tasks import upload_task
from survey.views.location_widget import LocationWidget
from survey.views.views_helper import contains_key


@login_required
@permission_required('auth.can_view_batches')
def upload(request):
    upload_form = UploadWeightsForm()
    if request.method == 'POST':
        upload_form = UploadWeightsForm(request.POST, request.FILES)
        if upload_form.is_valid():
            upload_task.delay(upload_form)
            messages.warning(request, "Upload in progress. This could take a while.")
            return HttpResponseRedirect('/locations/weights/upload/')

    context = {'button_label': 'Upload', 'id': 'upload-location-weights-form',
               'upload_form': upload_form, 'location_types': LocationType.objects.all(), 'range': range(3)}

    return render(request, 'locations/weights/upload.html', context)


def list_weights(request):
    location_weights = LocationWeight.objects.all()
    surveys = Survey.objects.all()
    survey = None
    selected_location = None
    params = request.GET
    if contains_key(params, 'survey'):
        survey = Survey.objects.get(id=params['survey'])
        location_weights = location_weights.filter(survey=survey)
    if contains_key(params, 'location'):
        selected_location = Location.objects.get(id=params['location'])
        location_weights = location_weights.filter(location=selected_location)

    location_types = LocationTypeDetails.get_ordered_types().exclude(name__iexact="country")
    context = {'location_weights': location_weights,
               'location_types': location_types,
               'location_data': LocationWidget(selected_location),
               'surveys': surveys,
               'selected_survey': survey,
               'action': 'list_weights_page',
               'request': request}
    return render(request, 'locations/weights/index.html', context)


def error_logs(request):
    location_weights_error_logs = UploadErrorLog.objects.filter(model='WEIGHTS')
    context = {'error_logs': location_weights_error_logs, 'request': request}

    return render(request, 'locations/weights/error_logs.html', context)