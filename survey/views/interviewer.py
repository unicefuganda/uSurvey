import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from survey.models import Location
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from survey.interviewer_configs import *
from survey.forms.interviewer import *
from survey.models import EnumerationArea
from survey.models.interviewer import Interviewer
from survey.views.location_widget import LocationWidget
from survey.utils.views_helper import contains_key
from survey.services.export_interviewers import ExportInterviewersService
from survey.utils.query_helper import get_filterset

CREATE_INTERVIEWER_DEFAULT_SELECT = ''
LIST_INTERVIEWER_DEFAULT_SELECT = 'All'


def _add_error_response_message(interviewer, request,action_text):
    error_message = "Interviewer not %s. " % action_text
    messages.error(request, error_message + "See errors below.")

    for field in interviewer.hidden_fields():
        if field.errors:
            messages.error(request, error_message + field.label + " information required.")

    if interviewer.non_field_errors():
        for err in interviewer.non_field_errors():
            messages.error(request, error_message + str(err))


def _process_form(interviewer_form, request, action_text,
                  redirect_url):
    if interviewer_form.is_valid():
        interviewer = interviewer_form.save()
        interviewer.remove_invalid_households()
        messages.success(request, "Interviewer successfully %s " % action_text)
        #update total number of households in ea if different
        if contains_key(request.POST, 'total_households'):
            selected_ea = interviewer.ea
            if selected_ea.total_households != int(request.POST['total_households']):
                selected_ea.total_households = request.POST['total_households']
                selected_ea.save()
        return HttpResponseRedirect(redirect_url)
    _add_error_response_message(interviewer_form, request,action_text)
    return None

@login_required
@permission_required('auth.can_view_interviewers')
def new_interviewer(request):
    interviewer = InterviewerForm(label_suffix='')
    selected_location = None
    selected_ea = None
    response = None

    if request.method == 'POST':
        interviewer = InterviewerForm(data=request.POST, label_suffix='')
        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST, 'location') else None
        selected_ea = EnumerationArea.objects.get(id=request.POST['ea']) if contains_key(request.POST, 'ea') else None
        action_text = "registered."
        redirect_url = "/interviewers/"
        response = _process_form(interviewer, request, action_text, redirect_url)

    return response or render(request, 'interviewers/interviewer_form.html', {'country_phone_code': COUNTRY_PHONE_CODE,
                                                                  'locations': LocationWidget(selected_location, ea=selected_ea),
                                                                  'form': interviewer,
                                                                  'action': "/interviewers/new/",
                                                                  'title': 'New Interviewer',
                                                                  'id': "create-interviewer-form",
                                                                  'class': 'interviewer-form',
                                                                  'button_label': "Create",
                                                                  'cancel_url': '/interviewers/',
                                                                  'loading_text': "Creating..."})

@login_required
def get_locations(request):
    tree_parent = request.GET['parent'] if request.GET.has_key('parent') and request.GET['parent'].isdigit() else None
    locations = Location.objects.filter(tree_parent=tree_parent)
    location_hash = {}
    for location in locations:
        location_hash[location.name] = location.id
    return HttpResponse(json.dumps(location_hash), content_type="application/json")

@login_required
@permission_required('auth.can_view_interviewers')
def list_interviewers(request):
    params = request.GET
    selected_location = None
    selected_ea = None
    interviewers = Interviewer.objects.order_by('id')
    search_fields = ['name', 'mobile_number']
    if request.GET.has_key('q'):
        interviewers = get_filterset(interviewers, request.GET['q'], search_fields)
    if params.has_key('status'):
        interviewers = interviewers.filter(is_blocked=ast.literal_eval(params['status']))
    if params.has_key('location') and params['location'].isdigit():
        selected_location = Location.objects.get(id=int(params['location']))
        corresponding_locations = selected_location.get_descendants(include_self=True)
        interviewers = interviewers.filter(ea__locations__in=corresponding_locations)

    if params.has_key('ea') and params['ea'].isdigit():
        selected_ea = EnumerationArea.objects.get(id=int(params['ea']))
        interviewers = interviewers.filter(ea=selected_ea)

    if not interviewers:
        location_type = selected_location.type.name.lower() if selected_location and selected_location.type else 'location'
        messages.error(request, "There are  no interviewers currently registered  for this %s." % location_type)

    location_widget = LocationWidget(selected_location, ea=selected_ea)
    return render(request, 'interviewers/index.html',
                  {'interviewers': interviewers,
                   'location_data': location_widget,
                   'request': request})


@login_required
@permission_required('survey.view_completed_survey')
def show_completion_summary(request, interviewer_id):
    interviewer = Interviewer.objects.get(pk=interviewer_id)
    return render(request, 'interviewers/completion_summary.html', {'interviewer': interviewer})

@login_required
def check_mobile_number(request):
    response = Interviewer.objects.filter(mobile_number=request.GET['mobile_number']).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")

@permission_required('auth.can_view_interviewers')
def show_interviewer(request, interviewer_id):
    interviewer = Interviewer.objects.get(id=interviewer_id)
    return render(request, 'interviewers/show.html', {'interviewer': interviewer, 'cancel_url': '/interviewers/'})

@permission_required('auth.can_view_interviewers')
def edit_interviewer(request, interviewer_id):
    response = None
    interviewer = Interviewer.objects.get(id=interviewer_id)
    selected_location = interviewer.location
    selected_ea = interviewer.ea
    interviewer_form = InterviewerForm(instance=interviewer, initial= {'confirm_mobile_number':interviewer.mobile_number})
    if request.method == 'POST':
        interviewer_form = InterviewerForm(data=request.POST, instance=interviewer)
        action_text = "edited."
        redirect_url = "/interviewers/"
        selected_location = Location.objects.get(id=request.POST['location']) if contains_key(request.POST, 'location') else None
        selected_ea = EnumerationArea.objects.get(id=request.POST['ea']) if contains_key(request.POST, 'ea') else None
        response = _process_form(interviewer_form, request, action_text, redirect_url)

    context = { 'action': '/interviewers/%s/edit/' % interviewer_id,
                'country_phone_code': COUNTRY_PHONE_CODE,
                'title': 'Edit Interviewer',
                'id': 'edit-interviewer-form',
                'class': 'interviewer-form',
                'button_label': 'Save',
                'cancel_url': '/interviewers/',
                'loading_text': 'Saving...',
                'form': interviewer_form,
                'locations': LocationWidget(selected_location, ea=selected_ea)}
    return response or render(request, 'interviewers/interviewer_form.html', context)

@permission_required('auth.can_view_interviewers')
def block_interviewer(request, interviewer_id):
    try:
        interviewer = Interviewer.objects.get(id=interviewer_id)
        interviewer.is_blocked = True
        interviewer.save()
        interviewer.households.clear()
        messages.success(request, "Interviewer successfully blocked.")
    except Interviewer.DoesNotExist:
        messages.error(request, "Interviewer does not exist.")
    return HttpResponseRedirect('/interviewers/')

@permission_required('auth.can_view_interviewers')
def unblock_interviewer(request, interviewer_id):
    try:
        interviewer = Interviewer.objects.get(id=interviewer_id)
        interviewer.is_blocked = False
        interviewer.save()
        messages.success(request, "Interviewer successfully unblocked.")
    except Interviewer.DoesNotExist:
        messages.error(request, "Interviewer does not exist.")
    return HttpResponseRedirect('/interviewers/')

@permission_required('auth.can_view_interviewers')
def download_interviewers(request):
    filename = 'all_interviewers'
    formatted_responses = ExportInterviewersService(settings.INTERVIEWER_EXPORT_HEADERS).formatted_responses()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    response.write("\r\n".join(formatted_responses))
    return response
