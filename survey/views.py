from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render, redirect
from investigator_configs import *
from rapidsms.contrib.locations.models import *
from survey.forms import *
from survey.models import Investigator
import json
from django.views.decorators.csrf import csrf_exempt
from survey.ussd import USSD
from django.contrib import messages
from django.utils.datastructures import SortedDict

CREATE_INVESTIGATOR_DEFAULT_SELECT=''
LIST_INVESTIGATOR_DEFAULT_SELECT='All'

def initialize_location_type(default_select=CREATE_INVESTIGATOR_DEFAULT_SELECT):
  selected_location = SortedDict()
  all_type= LocationType.objects.all()
  for location_type in all_type:
    selected_location[location_type.name]={ 'value': '', 'text':default_select, 'siblings':[]}
    
  selected_location[all_type[0].name]['siblings']= Location.objects.filter(tree_parent=None).order_by('name')
  return selected_location  

def assign_ancestors_locations(selected_location, location):
  ancestors = location.get_ancestors(include_self=True)
  for loca in ancestors:
    selected_location[loca.type.name]['value'] = loca.id
    all_default_select = selected_location[loca.type.name]['text']
    selected_location[loca.type.name]['text'] = loca.name
    siblings = list(loca.get_siblings().order_by('name'))
    siblings.insert(0, {'id':'', 'name':all_default_select})
    selected_location[loca.type.name]['siblings'] = siblings
  return selected_location  

def assign_immediate_child_locations(selected_location, location):
  children = location.get_descendants()
  if children:
    immediate_child = children[0]
    siblings = list(immediate_child.get_siblings(include_self=True).order_by('name'))
    selected_location[immediate_child.type.name]['siblings'] =  siblings
  return selected_location  

def update_location_type(selected_location, location_id):
  if not location_id:
    return selected_location
  location =  Location.objects.get(id=location_id)
  selected_location = assign_ancestors_locations(selected_location, location)
  selected_location = assign_immediate_child_locations(selected_location, location)
  return selected_location  

def new_investigator(request, 
                      investigator = InvestigatorForm(auto_id='investigator-%s', label_suffix=''),
                      location_type = initialize_location_type()):
                      
    list_of_eductional_levels = [education[0] for education in LEVEL_OF_EDUCATION]
    list_of_languages = [language[0] for language in LANGUAGES]

    investigator.fields = _put_confirm_mobile_number_exactly_after_mobile_number(investigator.fields)

    return render(request, 'investigators/new.html', {'list_of_eductional_levels': list_of_eductional_levels, 
                                                      'list_of_languages': list_of_languages,
                                                      'country_phone_code': COUNTRY_PHONE_CODE,
                                                      'form': investigator,
                                                      'location_type': location_type})

def _insert_confirm_field_right_after_mobile_number(keys):
  keys.remove('confirm_mobile_number')
  index_of_mobile_number = keys.index('mobile_number')
  keys.insert(index_of_mobile_number+1, 'confirm_mobile_number')
  return keys
                                                      
def _put_confirm_mobile_number_exactly_after_mobile_number(fields):
  rearranged_keys = _insert_confirm_field_right_after_mobile_number(fields.keys())
  new_fields = SortedDict()
  for key in rearranged_keys:
    new_fields[key]=fields[key]
  return new_fields  

def get_locations(request):
    tree_parent= request.GET['parent'] if request.GET['parent'] else None if request.GET.has_key('parent') else None 
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

def _get_posted_location(location_data):
  location_id=''
  for location_type in LocationType.objects.all():
    if location_data[location_type.name.lower()]:
      location_id=location_data[location_type.name.lower()]
  return location_id
    

def create_investigator(request):
    investigator = InvestigatorForm(request.POST)
    if investigator.is_valid():
      investigator.save()
      messages.success(request, "Investigator successfully registered.")
      return HttpResponseRedirect("/investigators/")

    location_id = _get_posted_location(request.POST)
    location_type = update_location_type(initialize_location_type(), location_id)
    
    error_message = "Investigator not registered. "
    done = False
    for field in investigator.hidden_fields():
      if field.errors:
        print field.label
        messages.error(request, error_message + field.label + " information required.")
        done = True
    
    if done:
      return new_investigator(request=request,
                              investigator=InvestigatorForm(data=request.POST, auto_id='investigator-%s', label_suffix=''),
                              location_type=location_type)       
        
    if investigator.non_field_errors():
      for err in investigator.non_field_errors():
        messages.error(request, error_message + str(err))
      return new_investigator(request=request,
                                investigator=InvestigatorForm(data=request.POST, auto_id='investigator-%s', label_suffix=''),
                                location_type=location_type)       
      
        
    messages.error(request, error_message + "See errors below.")
    return new_investigator(request=request,
                            investigator=InvestigatorForm(data=request.POST, auto_id='investigator-%s', label_suffix=''),
                            location_type=location_type)       

def list_investigators(request):
    selected_location = initialize_location_type(default_select=LIST_INVESTIGATOR_DEFAULT_SELECT)
    investigators = Investigator.objects.all()

    return render(request, 'investigators/index.html',
                          {'investigators': investigators,
                           'location_type': selected_location,
                           'request': request})

def filter_list_investigators(request, location_id):
   corresponding_locations = Location.objects.get(id=int(location_id)).get_descendants()
   investigators = Investigator.objects.filter(location__in=corresponding_locations)
   
   return_selected_location = update_location_type(initialize_location_type(default_select=LIST_INVESTIGATOR_DEFAULT_SELECT), location_id)

   return render(request, 'investigators/index.html',
                         {'investigators': investigators,
                          'location_type': return_selected_location,
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
        response = USSD(investigator, params).response()
    except Investigator.DoesNotExist:
        response = USSD.investigator_not_registered_response()
    template = "ussd/%s.txt" % USSD_PROVIDER
    return render(request, template, response)
