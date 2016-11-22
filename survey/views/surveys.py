import ast
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from survey.models import Survey, Location, LocationType, Batch
from survey.forms.surveys import SurveyForm
from survey.views.custom_decorators import handle_object_does_not_exist
from survey.utils.query_helper import get_filterset
from survey.models import EnumerationArea, LocationType, Location, BatchCommencement, SurveyHouseholdListing
from survey.forms.enumeration_area import EnumerationAreaForm, LocationsFilterForm
from django.conf import settings


@permission_required('auth.can_view_batches')
def index(request):
    surveys = Survey.objects.all().order_by('created')
    search_fields = ['name', 'description']
    if request.GET.has_key('q'):
        surveys = get_filterset(surveys, request.GET['q'], search_fields)
    if request.GET.has_key('type'):
        surveys = surveys.filter(type=ast.literal_eval(request.GET['type']))
    if request.GET.has_key('isopen'):
        surveys = surveys.filter(type=ast.literal_eval(request.GET['isopen']))
    context = {'surveys': surveys, 'request': request,
               'placeholder': 'name, description',
               'survey_form': SurveyForm(), 'batch_model': Batch}
    return render(request, 'surveys/index.html',
                  context)
#
# @permission_required('auth.can_view_batches')
# def manage(request, survey_id):
#     '''
#     Page to enable listing to
#     :param request:
#     :return:
#     '''
#     survey = get_object_or_404(Survey, id=survey_id)
#     if request.method == 'POST':
#         action = request.POST['action']
#         eas = EnumerationArea.objects.filter(id__in=request.POST.getlist('eas'))
#         if action.lower() == 'enable all':
#             survey.bulk_enable_batches(eas)
#         if action.lower() == 'disable all':
#             survey.bulk_disable_batches(eas)
#     locations_filter = LocationsFilterForm(data=request.GET)
#     enumeration_areas = locations_filter.get_enumerations()
#     search_fields = ['name', 'locations__name', ]
#     if request.GET.has_key('q'):
#         enumeration_areas = get_filterset(enumeration_areas, request.GET['q'], search_fields)
#     if request.GET.has_key('status'):
#         rs = list(survey.commencement_registry.all())
#         enabled_eas = [r.ea.id for r in rs]
#         if request.GET['status'] == 'enabled':
#             enumeration_areas = enumeration_areas.filter(id__in=enabled_eas)
#         else:
#             enumeration_areas = enumeration_areas.exclude(id__in=enabled_eas)
#     loc_types = LocationType.objects.exclude(pk=LocationType.smallest_unit().pk).exclude(parent__isnull=True)
#     context = {'enumeration_areas': enumeration_areas,
#                'locations_filter' : locations_filter,
#                'location_filter_types' : loc_types,
#                'survey' : survey,
#                'max_display_per_page': settings.MAX_DISPLAY_PER_PAGE}
#     request.breadcrumbs([
#         ('Surveys', reverse('survey_list_page')),
#     ])
#     return render(request, 'surveys/show.html', context)


@permission_required('auth.can_view_batches')
def new(request):
    response = None
    survey_form = SurveyForm()

    if request.method == 'POST':
        survey_form = SurveyForm(request.POST)
        if survey_form.is_valid():
            Survey.save_sample_size(survey_form)
            messages.success(request, 'Survey successfully added.')
            response = HttpResponseRedirect('/surveys/')

    context = {'survey_form': survey_form,
               'title': "New Survey",
               'button_label': 'Create',
               'id': 'add-survey-form',
               'action': "/surveys/new/",
               'cancel_url': '/surveys/',
               }
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
    ])
    return response or render(request, 'surveys/new.html', context)


@handle_object_does_not_exist(message="Survey does not exist.")
@permission_required('auth.can_view_batches')
def edit(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    survey_form = SurveyForm(instance=survey)
    if request.method == 'POST':
        survey_form = SurveyForm(instance=survey, data=request.POST)
        if survey_form.is_valid():
            Survey.save_sample_size(survey_form)
            messages.success(request, 'Survey successfully edited.')
            return HttpResponseRedirect('/surveys/')

    context = {'survey_form': survey_form,
               'title': "Edit Survey",
               'button_label': 'Save',
               'id': 'edit-survey-form',
               'cancel_url': '/surveys/',
               'action': '/surveys/%s/edit/' % survey_id
               }
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
    ])
    return render(request, 'surveys/new.html', context)


@handle_object_does_not_exist(message="Survey does not exist.")
@permission_required('auth.can_view_batches')
def delete(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    if SurveyHouseholdListing.objects.filter(survey=survey).exists():
        messages.error(request, "Survey cannot be deleted.")
    else:
        survey.delete()
    return HttpResponseRedirect('/surveys/')
