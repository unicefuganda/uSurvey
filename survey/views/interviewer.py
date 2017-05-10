import json
import ast
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.forms.models import inlineformset_factory
from survey.forms.interviewer import InterviewerForm,\
    USSDAccessForm, ODKAccessForm
from survey.models import EnumerationArea
from survey.models import LocationType
from survey.models import Interviewer
from survey.models import USSDAccess
from survey.services.export_interviewers import ExportInterviewersService
from survey.utils.query_helper import get_filterset
from survey.forms.enumeration_area import LocationsFilterForm

CREATE_INTERVIEWER_DEFAULT_SELECT = ''
LIST_INTERVIEWER_DEFAULT_SELECT = 'All'


def _add_error_response_message(interviewer, request, action_text):
    error_message = "Interviewer not %s. " % action_text
    messages.error(request, error_message + "See errors below.")


def _create_or_edit(
        request,
        action_text,
        interviewer_id=None,
        interviewer=None):
    extra = 1
    request.breadcrumbs([
        ('Interviewers', reverse('interviewers_page')),
    ])
    extra = 1
    title = 'New Interviewer'
    odk_instance = None
    # loc_data = request.GET if request.method == 'GET' else request.POST
    data = request.GET if request.method == 'GET' else request.POST
    if request.POST and request.POST.get('ea'):
        ea = get_object_or_404(EnumerationArea, pk=request.POST['ea'])
        data = dict([(loc.type.name, loc.pk) for loc in ea.parent_locations()])
    if interviewer:
        title = 'Edit Interviewer'
        odk_accesses = interviewer.odk_access
        if odk_accesses.exists():
            odk_instance = odk_accesses[0]
        data = data or dict([(loc.type.name, loc.pk)
                             for loc in interviewer.ea.parent_locations()])
        if interviewer.ussd_access.exists():
            extra = 0
    locations_filter = LocationsFilterForm(data=data)
    eas = EnumerationArea.objects.none()
    USSDAccessFormSet = inlineformset_factory(Interviewer, USSDAccess, form=USSDAccessForm, extra=extra)
    ussd_access_form = USSDAccessFormSet(prefix='ussd_access', instance=interviewer)
    response = None
    redirect_url = reverse('interviewers_page')
    odk_access_form = ODKAccessForm(instance=odk_instance)
    if request.method == 'POST':
        interviewer_form = InterviewerForm(eas, data=request.POST, instance=interviewer)
        ussd_access_form = USSDAccessFormSet(
            request.POST,
            prefix='ussd_access',
            instance=interviewer)
        odk_access_form = ODKAccessForm(request.POST, instance=odk_instance)
        if interviewer_form.is_valid() and odk_access_form.is_valid():
            interviewer = interviewer_form.save()
            ussd_access_form.instance = interviewer
            if ussd_access_form.is_valid():
                ussd_access_form.save()
                odk_access = odk_access_form.save(commit=False)
                odk_access.interviewer = interviewer
                odk_access.save()
                messages.success(
                    request, "Interviewer successfully %sed." % action_text)
            return HttpResponseRedirect(redirect_url)
    else:
        interviewer_form = InterviewerForm(eas, instance=interviewer)
    loc_types = LocationType.in_between()
    return response or render(request, 'interviewers/interviewer_form.html', {
        'form': interviewer_form,
        'ussd_access_form': ussd_access_form,
        'odk_access_form': odk_access_form,
        'title': title,
        'id': "create-interviewer-form",
        'class': 'interviewer-form',
        'button_label': "Save",
        'cancel_url': redirect_url,
        'locations_filter': locations_filter,
        'location_filter_types': loc_types,
        'loading_text': "Creating...",
        'mode': action_text,
        'interviewer_id': interviewer_id
    })


@login_required
@permission_required('auth.can_view_interviewers')
def new_interviewer(request):
    return _create_or_edit(request, 'Register')


@login_required
@permission_required('auth.can_view_interviewers')
def edit_interviewer(request, interviewer_id=None, mode=None):
    return _create_or_edit(
        request,
        mode,
        interviewer_id,
        interviewer=get_object_or_404(
            Interviewer,
            pk=interviewer_id))


@login_required
@permission_required('auth.can_view_interviewers')
def list_interviewers(request):
    params = request.GET
    locations_filter = LocationsFilterForm(data=request.GET, include_ea=True)
    if locations_filter.is_valid():
        interviewers = Interviewer.objects.filter(
            ea__in=locations_filter.get_enumerations())
    else:
        interviewers = Interviewer.objects.all()
    search_fields = ['name', 'intervieweraccess__user_identifier']
    if 'q' in request.GET:
        interviewers = get_filterset(
            interviewers, request.GET['q'], search_fields)
    if 'status' in params:
        interviewers = interviewers.filter(
            is_blocked=ast.literal_eval(params['status']))
    loc_types = LocationType.in_between()
    return render(request, 'interviewers/index.html',
                  {'interviewers': interviewers.order_by('name'),
                   'locations_filter': locations_filter,
                   'location_filter_types': loc_types,
                   'placeholder': 'name, mobile numbers, odk id',
                   'request': request})


@login_required
@permission_required('survey.view_completed_survey')
def show_completion_summary(request, interviewer_id):
    interviewer = Interviewer.objects.get(pk=interviewer_id)
    request.breadcrumbs([
        ('Interviewers', reverse('interviewers_page')),
    ])
    return render(request,
                  'interviewers/completion_summary.html',
                  {'interviewer': interviewer})


@login_required
def check_mobile_number(request):
    response = Interviewer.objects.filter(
        mobile_number=request.GET['mobile_number']).exists()
    return HttpResponse(
        json.dumps(
            not response),
        content_type="application/json")


@permission_required('auth.can_view_interviewers')
def show_interviewer(request, interviewer_id):
    interviewer = Interviewer.objects.get(id=interviewer_id)
    return render(request, 'interviewers/show.html',
                  {'interviewer': interviewer, 'cancel_url': '/interviewers/'})


@permission_required('auth.can_view_interviewers')
def block_interviewer(request, interviewer_id):
    try:
        interviewer = Interviewer.objects.get(id=interviewer_id)
        interviewer.ussd_access.update(is_active=False)
        interviewer.odk_access.update(is_active=False)
        interviewer.is_blocked = True
        interviewer.save()
        messages.success(
            request, "Interviewer USSD Access successfully blocked.")
    except Interviewer.DoesNotExist:
        messages.error(request, "Interviewer does not exist.")
    return HttpResponseRedirect(reverse('interviewers_page'))


@permission_required('auth.can_view_interviewers')
def unblock_interviewer(request, interviewer_id):
    try:
        interviewer = Interviewer.objects.get(id=interviewer_id)
        interviewer.ussd_access.update(is_active=True)
        interviewer.odk_access.update(is_active=True)
        interviewer.is_blocked = False
        interviewer.save()
        messages.success(
            request, "Interviewer USSD Access successfully unblocked.")
    except Interviewer.DoesNotExist:
        messages.error(request, "Interviewer does not exist.")
    return HttpResponseRedirect(reverse('interviewers_page'))


@permission_required('auth.can_view_interviewers')
def block_ussd(request, interviewer_id):
    try:
        interviewer = Interviewer.objects.get(id=interviewer_id)
        interviewer.ussd_access.update(is_active=False)
        messages.success(
            request, "Interviewer USSD Access successfully blocked.")
    except Interviewer.DoesNotExist:
        messages.error(request, "Interviewer does not exist.")
    return HttpResponseRedirect(reverse('interviewers_page'))


@permission_required('auth.can_view_interviewers')
def unblock_ussd(request, interviewer_id):
    try:
        interviewer = Interviewer.objects.get(id=interviewer_id)
        interviewer.ussd_access.update(is_active=True)
        messages.success(
            request, "Interviewer USSD Access successfully unblocked.")
    except Interviewer.DoesNotExist:
        messages.error(request, "Interviewer does not exist.")
    return HttpResponseRedirect(reverse('interviewers_page'))


@permission_required('auth.can_view_interviewers')
def block_odk(request, interviewer_id):
    try:
        interviewer = Interviewer.objects.get(id=interviewer_id)
        interviewer.odk_access.update(is_active=False)
        messages.success(
            request, "Interviewer USSD Access successfully blocked.")
    except Interviewer.DoesNotExist:
        messages.error(request, "Interviewer does not exist.")
    return HttpResponseRedirect(reverse('interviewers_page'))


@permission_required('auth.can_view_interviewers')
def unblock_odk(request, interviewer_id):
    try:
        interviewer = Interviewer.objects.get(id=interviewer_id)
        interviewer.odk_access.update(is_active=True)
        messages.success(
            request, "Interviewer USSD Access successfully unblocked.")
    except Interviewer.DoesNotExist:
        messages.error(request, "Interviewer does not exist.")
    return HttpResponseRedirect(reverse('interviewers_page'))


@permission_required('auth.can_view_interviewers')
def download_interviewers(request):
    filename = 'all_interviewers'
    formatted_responses = ExportInterviewersService(
        settings.INTERVIEWER_EXPORT_HEADERS).formatted_responses()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; \
        filename="%s.csv"' % filename
    response.write("\r\n".join(formatted_responses))
    return response
