from django.http import HttpResponse
from django.shortcuts import render_to_response, render, redirect
from investigator_configs import *
from rapidsms.contrib.locations.models import *
from survey.forms import *
from survey.models import Investigator
import json
from django.views.decorators.csrf import csrf_exempt

def new_investigator(request):
    list_of_eductional_levels = [education[0] for education in LEVEL_OF_EDUCATION]
    list_of_languages = [language[0] for language in LANGUAGES]
    investigator = InvestigatorForm()
      
    return render(request, 'investigators/new.html', {'list_of_eductional_levels': list_of_eductional_levels, 
                                                      'list_of_languages': list_of_languages,
                                                      'country_phone_code': COUNTRY_PHONE_CODE,
                                                      'form': investigator,
                                                      'location_type': LocationType.objects.all()})

def get_locations(request):
    tree_parent= request.GET['parent'] if request.GET.has_key('parent') else None
    locations = Location.objects.filter(tree_parent=tree_parent)
    location_hash = {}
    for location in locations:
        location_hash[location.name] = location.id
    return HttpResponse(json.dumps(location_hash), content_type="application/json")

def create_or_list_investigators(request):
    if request.method == 'POST':
        return create_investigator(request)
    else:
        return list_investigators(request)

def create_investigator(request):
    investigator = InvestigatorForm(request.POST)
    investigator.save()
    return HttpResponse(status=201)

def initialize_location_type():
  selected_location = {}
  for location_type in LocationType.objects.all():
    selected_location[location_type.name]={ 'value': '', 'text':'All'}
  return selected_location  

def no_location_selected(location):
  return location.__class__.__name__=='QuerySet'

def update_location_type(selected_location, location):
  if no_location_selected(location):
    return selected_location
    
  assigned_type = location.get_ancestors(include_self=True)
  for loca in assigned_type:
    selected_location[loca.type.name]['value'] = loca.id
    selected_location[loca.type.name]['text'] = loca.name
    
  return selected_location  


def list_investigators(request):
    selected_location = initialize_location_type()
    location= request.GET['parent'] if request.GET.has_key('parent') else Location.objects.all()
    investigators = Investigator.objects.filter(location__in=location)
    selected_location = update_location_type(selected_location, location)

    return render(request, 'investigators/index.html', 
                          {'investigators': investigators,
                           'location_type': LocationType.objects.all(),
                           'request': request})

def check_mobile_number(request):
    response = Investigator.objects.filter(mobile_number = request.GET['mobile_number']).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

@csrf_exempt
def ussd(request):
    params = request.POST if request.method == 'POST' else request.GET
    mobile_number = params['msisdn'].replace(COUNTRY_PHONE_CODE, '')
    try:
        investigator = Investigator.objects.get(mobile_number=mobile_number)
        responseString = "Welcome %s. You can now start to collect responses on survey questions." % investigator.name
        template = "ussd/%s.txt" % USSD_PROVIDER
        return render(request, template, { 'action': 'end', 'responseString': responseString })
    except Investigator.DoesNotExist:
        return HttpResponse(status=404)
