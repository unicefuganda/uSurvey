import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from survey.models import QuestionLoop
from survey.models import Survey, Location, LocationType
from survey.models import Batch
from survey.models import QuestionFlow
from survey.models import Survey
from survey.forms.question_set import BatchForm
from survey.forms.filters import BatchOpenStatusFilterForm
from .question_set import QuestionSetView
from survey.utils.query_helper import get_filterset


@login_required
@permission_required('auth.can_view_batches')
def index(request, survey_id=None):
    if survey_id:
        survey = Survey.get(pk=survey_id)
    request.breadcrumbs(Batch.index_breadcrumbs(survey=survey))
    if survey_id is None:
        batches = Batch.objects.all()
    else:
        batches = Batch.objects.filter(survey__id=survey_id)
    qset_view = QuestionSetView(model_class=Batch)
    qset_view.questionSetForm = BatchForm
    return qset_view.index(
        request, batches, extra_context={
            'survey': survey}, initial={
            'survey': survey.pk})


@login_required
@permission_required('auth.can_view_batches')
def batches(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    batches = Batch.objects.filter(survey__id=survey_id)
    batches = batches.values('id', 'name').order_by('name')
    json_dump = json.dumps(list(batches), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')


@login_required
@permission_required('auth.can_view_batches')
def show(request, survey_id, batch_id):
    batch = Batch.objects.get(id=batch_id)
    open_status_filter = BatchOpenStatusFilterForm(batch, request.GET)
    batch_location_ids = batch.open_locations.values_list(
        'location_id', flat=True)
    locations = open_status_filter.get_locations()
    search_fields = ['name', ]
    if 'q' in request.GET:
        locations = get_filterset(locations, request.GET['q'], search_fields)
    request.breadcrumbs(Batch.edit_breadcrumbs(survey=batch.survey))
    open_locations = locations.filter(id__in=batch_location_ids)
    non_response_active_locations = batch.get_non_response_active_locations()
    context = {
        'batch': batch,
        'locations': locations,
        'open_locations': open_locations,
        'open_status_filter': open_status_filter,
        'non_response_active_locations': non_response_active_locations
        }
    return render(request, 'batches/show.html', context)


@login_required
@permission_required('auth.can_view_batches')
def all_locs(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    action = request.POST['action']
    locations = Location.objects.filter(
        type=LocationType.largest_unit()).order_by('name')
    if action.lower() == 'open all':
        for location in locations:
            batch.open_for_location(location)
    if action.lower() == 'close all':
        for location in locations:
            batch.close_for_location(location)
    return HttpResponseRedirect(
        reverse(
            'batch_show_page',
            args=(
                batch.survey.id,
                batch_id,
            )))


@login_required
@permission_required('auth.can_view_batches')
def open(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    location = Location.objects.get(id=request.POST['location_id'])
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
    survey = Survey.objects.get(id=survey_id)
    qset_view = QuestionSetView(model_class=Batch)
    qset_view.questionSetForm = BatchForm
    request.breadcrumbs(Batch.new_breadcrumbs(survey=survey))
    response = qset_view.new(
        request, extra_context={
            'survey': survey}, initial={
            'survey': survey.pk})
    if response.status_code == 302:
        response = HttpResponseRedirect(
            reverse('batch_index_page', args=(survey.pk, )))
    return response


@permission_required('auth.can_view_batches')
def edit(request, batch_id):
    batch = Batch.get(pk=batch_id)
    survey = batch.survey
    qset_view = QuestionSetView(model_class=Batch)
    qset_view.questionSetForm = BatchForm
    breadcrumbs = Batch.edit_breadcrumbs(survey=survey)
    cancel_url = '../'
    if breadcrumbs:
        request.breadcrumbs(breadcrumbs)
        cancel_url = breadcrumbs[-1][1]
    response = qset_view.edit(
        request, batch, extra_context={
            'cancel_url': cancel_url}, initial={
            'survey': survey.pk})
    if response.status_code == 302:
        response = HttpResponseRedirect(
            reverse('batch_index_page', args=(survey.pk, )))
    return response


def _add_success_message(request, action_str):
    messages.success(request, 'Batch successfully %s.' % action_str)


@permission_required('auth.can_view_batches')
def delete(request, survey_id, batch_id):
    try:
        batch = Batch.get(id=batch_id)
        QuestionSetView(model_class=Batch).delete(request, batch)
    except Batch.DoesNotExist:
        pass
    return HttpResponseRedirect(
        reverse(
            'batch_index_page',
            args=(
                batch.survey.id,
            )))


@permission_required('auth.can_view_batches')
def update_orders(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    new_orders = request.POST.getlist('order_information', None)
    if len(new_orders) > 0:
        # wipe off present inline flows
        inlines = batch.questions_inline()
        start_question = inlines.pop(0)
        question = start_question
        for next_question in inlines:
            QuestionFlow.objects.filter(
                question=question, next_question=next_question).delete()
            question = next_question
        order_details = []
        map(lambda order: order_details.append(order.split('-')), new_orders)
        order_details = sorted(
            order_details, key=lambda detail: int(detail[0]))
        # recreate the flows
        questions = batch.questions.all()
        if questions:  # so all questions can be fetched once and cached
            question_id = order_details.pop(0)[1]
            start_question = questions.get(pk=question_id)
            for order, next_question_id in order_details:
                QuestionFlow.objects.create(
                    question=questions.get(
                        pk=question_id), next_question=questions.get(
                        pk=next_question_id))
                question_id = next_question_id
            batch.start_question = start_question
            batch.save()
        # now remove any loop associated with this batch
        QuestionLoop.objects.filter(loop_starter__qset__id=batch_id).delete()
        success_message = "Question orders successfully\
        updated for batch: %s." % batch.name.capitalize()
        messages.success(request, success_message)
    else:
        messages.error(request, 'No questions orders were updated.')
    return HttpResponseRedirect("/batches/%s/questions/" % batch_id)


@login_required
def check_name(request, survey_id):
    response = Batch.objects.filter(
        name=request.GET['name'], survey__id=survey_id).exists()
    return HttpResponse(
        json.dumps(
            not response),
        content_type="application/json")


@permission_required('auth.can_view_batches')
def list_batches(request):
    if request.is_ajax():
        batches = Batch.objects.values('id', 'name').order_by('name')
        json_dump = json.dumps(list(batches), cls=DjangoJSONEncoder)
        return HttpResponse(json_dump, content_type='application/json')
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
    ])
    return render(request, 'layout.html')


@permission_required('auth.can_view_batches')
def list_all_questions(request):
    batch_id = request.GET.get('id', None)
    batch = Batch.get(pk=batch_id)
    # if request.is_ajax():
    json_dump = json.dumps(
        [{'id': q.id, 'identifier': q.identifier}
            for q in batch.all_questions], cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')
    return HttpResponseRedirect(
        reverse(
            'batch_index_page',
            args=(
                batch.survey.pk,
            )))


@permission_required('auth.can_view_batches')
def list_batch_questions(request):
    batch_id = request.GET.get('id', None)
    batch = Batch.get(pk=batch_id)
    if request.is_ajax():
        json_dump = json.dumps(
            [{'id': q.id, 'identifier': q.identifier}
                for q in batch.flow_questions], cls=DjangoJSONEncoder)
        return HttpResponse(json_dump, content_type='application/json')
    return HttpResponseRedirect(
        reverse(
            'batch_index_page',
            args=(
                batch.survey.pk,
            )))


def activate_non_response(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    location = Location.objects.get(
        id=request.POST['non_response_location_id'])
    if batch.is_open_for(location):
        batch.activate_non_response_for(location)
        return HttpResponse(json.dumps(""), content_type="application/json")
    message = "%s is not open for %s" % (batch.name, location.name)
    return HttpResponse(json.dumps(message), content_type="application/json")


def deactivate_non_response(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    location = Location.objects.get(
        id=request.POST['non_response_location_id'])
    if batch.is_open_for(location):
        batch.deactivate_non_response_for(location)
    return HttpResponse(json.dumps(""), content_type="application/json")
