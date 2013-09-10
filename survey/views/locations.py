from django.http import HttpResponse, HttpResponseRedirect
from rapidsms.contrib.locations.models import Location, LocationType
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from survey.forms.locations import LocationTypeForm, LocationForm
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages

@login_required
def children(request, location_id):
    location = Location.objects.get(id=location_id)
    children = location.get_children().values('id', 'name').order_by('name')
    json_dump = json.dumps(list(children), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')

@permission_required('auth.can_view_locations')
def new_type(request):
    response = None
    type_form = LocationTypeForm()
    if request.method == 'POST':
        type_form = LocationTypeForm(data=request.POST)
        if type_form.is_valid():
            type_form.save()
            messages.success(request, 'Location Type successfully added.')
    context = {'location_type_form': type_form,
                'button_label': 'Create',
                'title':'New Location Type',}
    return response or render(request, 'locations/type/new.html', context)

@permission_required('auth.can_view_locations')
def new(request):
    response = None
    location_form = LocationForm()
    if request.method == 'POST':
        location_form = LocationForm(data=request.POST)
        if location_form.is_valid():
            location_form.save()
            messages.success(request, 'Location successfully added.')
        else:
            messages.error(request, 'Location not added. %s'%location_form.errors['__all__'][0])

    context = {'location_form':location_form,
                'button_label': 'Create',
                'title':'New Location',}

    return response or render(request, 'locations/new.html', context)