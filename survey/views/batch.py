from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from rapidsms.contrib.locations.models import Location, LocationType
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages

from survey.investigator_configs import *
from survey.models import HouseholdMemberGroup, Question, QuestionModule, BatchQuestionOrder
from survey.models.surveys import Survey
from survey.models.batch import Batch, BatchLocationStatus

from survey.forms.batch import BatchForm, BatchQuestionsForm
import json


@login_required
@permission_required('auth.can_view_batches')
def index(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    batches = Batch.objects.filter(survey__id=survey_id)
    context = {'batches': batches, 'survey': survey,
               'request': request, 'batchform': BatchForm(instance=Batch(survey=survey)),
               'action': '/surveys/%s/batches/new/' % survey_id, }
    return render(request, 'batches/index.html',
                  context)


@login_required
@permission_required('auth.can_view_batches')
def show(request, survey_id, batch_id):
    batch = Batch.objects.get(id=batch_id)
    prime_location_type = LocationType.objects.get(name=PRIME_LOCATION_TYPE)
    locations = Location.objects.filter(type=prime_location_type).order_by('name')
    open_locations = Location.objects.filter(id__in=batch.open_locations.values_list('location_id', flat=True))
    return render(request, 'batches/show.html',
                  {'batch': batch, 'locations': locations, 'open_locations': open_locations})


@login_required
@permission_required('auth.can_view_batches')
def open(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    location = Location.objects.get(id=request.POST['location_id'])
    other_surveys = batch.other_surveys_with_open_batches_in(location)

    if other_surveys.count() > 0:
        message = "%s has already open batches from survey %s" % (location.name, other_surveys[0].name)
        return HttpResponse(json.dumps(message), content_type="application/json")
    else:
        locations = location.get_descendants(include_self=True)
        for location in locations:
            batch.open_for_location(location)
        return HttpResponse(json.dumps(""), content_type="application/json")


@login_required
@permission_required('auth.can_view_batches')
def close(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    location = Location.objects.get(id=request.POST['location_id'])
    batch.close_for_location(location)
    return HttpResponse(json.dumps(""), content_type="application/json")


@login_required
@permission_required('auth.can_view_batches')
def new(request, survey_id):
    batch = Batch(survey=Survey.objects.get(id=survey_id))
    batchform = BatchForm(instance=batch)
    return _process_form(request=request, batchform=batchform, action_str='added')


def _process_form(request, batchform, action_str='added', btn_label="Create"):
    if request.method == 'POST':
        batchform = BatchForm(data=request.POST, instance=batchform.instance)
        if batchform.is_valid():
            batch = batchform.save()
            _add_success_message(request, action_str)
            batch_list_url = '/surveys/%s/batches/' % str(batch.survey.id)
            return HttpResponseRedirect(batch_list_url)
    context = {'batchform': batchform, 'button_label': btn_label, 'id': 'add-batch-form', 'title': 'New Batch'}
    return render(request, 'batches/new.html', context)


@permission_required('auth.can_view_batches')
def edit(request, survey_id, batch_id):
    batchform = BatchForm(instance=Batch.objects.get(id=batch_id, survey__id=survey_id))
    return _process_form(request=request, batchform=batchform, action_str='edited', btn_label="Save")


def _add_success_message(request, action_str):
    messages.success(request, 'Batch successfully %s.' % action_str)


@permission_required('auth.can_view_batches')
def delete(request, survey_id, batch_id):
    batch = Batch.objects.get(id=batch_id)
    if not batch.can_be_deleted():
        messages.error(request, 'Batch cannot be deleted.')
    else:
        batch.delete()
        _add_success_message(request, 'deleted')
    return HttpResponseRedirect('/surveys/%s/batches/' % survey_id)


@permission_required('auth.can_view_batches')
def assign(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    batch_questions_form = BatchQuestionsForm(batch=batch)

    groups = HouseholdMemberGroup.objects.all().exclude(name='REGISTRATION GROUP')
    batch = Batch.objects.get(id=batch_id)
    if request.method == 'POST':
        batch_question_form = BatchQuestionsForm(batch=batch, data=request.POST, instance=batch)
        if batch_question_form.is_valid():
            batch_question_form.save()
            success_message = "Questions successfully assigned to batch: %s." % batch.name.capitalize()
            messages.success(request, success_message)
            return HttpResponseRedirect("/batches/%s/questions/" % batch_id)
    all_modules = QuestionModule.objects.all()
    context = {'batch_questions_form': batch_questions_form, 'batch': batch,
               'button_label': 'Save', 'id': 'assign-question-to-batch-form', 'groups': groups,
               'modules': all_modules}
    return render(request, 'batches/assign.html',
                  context)

@permission_required('auth.can_view_batches')
def update_orders(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    new_orders = request.POST.getlist('order_information', None)
    if new_orders:
        for new_order in new_orders:
            BatchQuestionOrder.update_question_order(new_order, batch)
        success_message = "Question orders successfully updated for batch: %s." % batch.name.capitalize()
        messages.success(request, success_message)
    else:
        messages.error(request, 'No questions orders were updated.')
    return HttpResponseRedirect("/batches/%s/questions/" % batch_id)

@login_required
def check_name(request, survey_id):
    response = Batch.objects.filter(name=request.GET['name'], survey__id=survey_id).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")
