from django.http import HttpResponse
from django.shortcuts import render_to_response, render, redirect
from investigator_configs import *
from rapidsms.contrib.locations.models import Location
import json

def new_investigator(request):
    return render(request, 'investigators/new.html', {'list_of_eductional_levels': LEVEL_OF_EDUCATION, 'list_of_languages': LANGUAGES })

def get_locations(request):
    locations = Location.objects.filter(name__icontains=request.GET['q'])
    location_hash = {}
    for location in locations:
        location_hash[location.auto_complete_text()] = location.id
    return HttpResponse(json.dumps(location_hash), content_type="application/json")
