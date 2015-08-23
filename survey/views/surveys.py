from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from survey.models.surveys import Survey
from survey.forms.surveys import SurveyForm
from survey.views.custom_decorators import handle_object_does_not_exist


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
               'survey_form': SurveyForm()}
    return render(request, 'surveys/index.html',
                  context)

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
               'action': '/surveys/%s/edit/' %survey_id
               }
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
    ])
    return render(request, 'surveys/new.html', context)

@handle_object_does_not_exist(message="Survey does not exist.")
@permission_required('auth.can_view_batches')
def delete(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    messages.error(request, "Survey cannot be deleted.")
    return HttpResponseRedirect('/surveys/')
