from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from survey.models.surveys import Survey
from survey.forms.surveys import SurveyForm


@permission_required('auth.can_view_batches')
def index(request):
    surveys = Survey.objects.all().order_by('created')
    return render(request, 'surveys/index.html',
                  {'surveys': surveys, 'request': request})

@permission_required('auth.can_view_batches')
def new(request):
    response = None
    survey_form = SurveyForm()

    if request.method == 'POST':
        survey_form = SurveyForm(request.POST)
        if survey_form.is_valid():
            survey_form.save()
            messages.success(request, 'Survey successfully added.')
            response = HttpResponseRedirect('/surveys/')

    context = {'survey_form': survey_form,
               'title': "New Survey",
               'button_label': 'Save',
               'id': 'add-survey-form',
               'action': "/surveys/new/",
               }

    return response or render(request, 'surveys/new.html', context)
