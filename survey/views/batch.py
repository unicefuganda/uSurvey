import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from survey.interviewer_configs import *
from survey.models import HouseholdMemberGroup, QuestionModule
from survey.models import Survey, Location, LocationType
from survey.models import Survey, Batch, QuestionTemplate, QuestionFlow, QuestionOption
from survey.models import BatchQuestion as Question
from survey.forms.batch import BatchQuestionsForm
from survey.forms.question_set import BatchForm
from survey.forms.filters import QuestionFilterForm
from .question_set import QuestionSetView


@login_required
@permission_required('auth.can_view_batches')
def index(request, survey_id=None):
    survey = Survey.get(pk=survey_id)
    request.breadcrumbs(Batch.index_breadcrumbs(survey=survey))
    if survey_id is None:
        batches = Batch.objects.all()
    else:
        batches = Batch.objects.filter(survey__id=survey_id)
    qset_view = QuestionSetView(model_class=Batch)
    qset_view.questionSetForm = BatchForm
    return qset_view.index(request, batches, extra_context={'survey': survey}, initial={'survey': survey.pk})


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
    prime_location_type = LocationType.largest_unit()
    locations = Location.objects.filter(
        type=prime_location_type).order_by('name')
    batch_location_ids = batch.open_locations.values_list(
        'location_id', flat=True)
    if request.GET.has_key('status'):
        if request.GET['status'] == 'open':
            locations = locations.filter(id__in=batch_location_ids)
        else:
            locations = locations.exclude(id__in=batch_location_ids)
    request.breadcrumbs(Batch.edit_breadcrumbs(survey=batch.survey))
    open_locations = locations.filter(id__in=batch_location_ids)
    context = {'batch': batch,
               'locations': locations,
               'open_locations': open_locations,
               'non_response_active_locations': batch.get_non_response_active_locations()}
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
    return HttpResponseRedirect(reverse('batch_show_page', args=(batch.survey.id, batch_id, )))


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
    response = qset_view.new(request, extra_context={'survey': survey}, initial={'survey': survey.pk})
    if response.status_code == 302:
        response = HttpResponseRedirect(reverse('batch_index_page', args=(survey.pk, )))
    return response

@permission_required('auth.can_view_batches')
def edit(request, batch_id):
    batch = Batch.get(pk=batch_id)
    survey = batch.survey
    qset_view = QuestionSetView(model_class=Batch)
    qset_view.questionSetForm = BatchForm
    request.breadcrumbs(Batch.edit_breadcrumbs(survey=survey))
    response = qset_view.edit(request, batch, initial={'survey': survey.pk})
    if response.status_code == 302 and response.url == '%s_home' % Batch.resolve_tag():
        response.url = reverse('batch_index_page', args=(survey.pk, ))
    return response


def _add_success_message(request, action_str):
    messages.success(request, 'Batch successfully %s.' % action_str)


@permission_required('auth.can_view_batches')
def delete(request, batch_id):
    try:
        batch = Batch.get(id=batch_id)
        QuestionSetView(model_class=Batch).delete(request, batch)
    except Batch.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse('batch_index_page', args=(batch.survey.id,)))


@permission_required('auth.can_view_batches')
def assign(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    if batch.is_open():
        error_message = "Questions cannot be assigned to open batch: %s." % batch.name.capitalize()
        messages.error(request, error_message)
        return HttpResponseRedirect("/batches/%s/questions/" % batch_id)
    batch_questions_form = BatchQuestionsForm(batch=batch)
    batch = Batch.objects.get(id=batch_id)
    groups = HouseholdMemberGroup.objects.all()
    groups.exists()
    modules = QuestionModule.objects.all()
    modules.exists()
    if request.method == 'POST':
        data = dict(request.POST)
        last_question = batch.last_question_inline()
        lib_questions = QuestionTemplate.objects.filter(
            identifier__in=data.get('identifier', ''))
        # print 'data: ', data, 'lib questions: ', lib_questions
        if lib_questions:
            for lib_question in lib_questions:
                question = Question.objects.create(identifier=lib_question.identifier,
                                                   text=lib_question.text,
                                                   answer_type=lib_question.answer_type,
                                                   #group=lib_question.group,
                                                   module=lib_question.module,
                                                   qset=batch,
                                                   )
                # assign the options
                for option in lib_question.options.all():
                    QuestionOption.objects.create(
                        question=question, text=option.text, order=option.order)
                if last_question:
                    QuestionFlow.objects.create(
                        question=last_question, next_question=question)
                else:
                    batch.start_question = question
                    batch.save()
                last_question = question
#         batch_questions_form = BatchQuestionsForm(batch=batch, data=request.POST, instance=batch)
        success_message = "Questions successfully assigned to batch: %s." % batch.name.capitalize()
        messages.success(request, success_message)
        return HttpResponseRedirect(reverse("batch_questions_page",  args=(batch_id, )))
    all_modules = QuestionModule.objects.all()
    used_identifiers = [
        question.identifier for question in batch.questions.all()]
    library_questions = QuestionTemplate.objects.exclude(
        identifier__in=used_identifiers).order_by('identifier')
    question_filter_form = QuestionFilterForm()
#     library_questions =  question_filter_form.filter(library_questions)
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
        (batch.survey.name, reverse('batch_index_page', args=(batch.survey.pk, ))),
        (batch.name, reverse('batch_questions_page', args=(batch.pk, ))),
    ])
    context = {'batch_questions_form': unicode(batch_questions_form), 'batch': batch,
               'button_label': 'Save', 'id': 'assign-question-to-batch-form', 'groups': groups,
               'library_questions': library_questions, 'question_filter_form': question_filter_form,
               'modules': all_modules}
    return render(request, 'batches/assign.html',
                  context)


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
                QuestionFlow.objects.create(question=questions.get(pk=question_id),
                                            next_question=questions.get(pk=next_question_id))
                question_id = next_question_id
            batch.start_question = start_question
            batch.save()

        success_message = "Question orders successfully updated for batch: %s." % batch.name.capitalize()
        messages.success(request, success_message)
    else:
        messages.error(request, 'No questions orders were updated.')
    return HttpResponseRedirect("/batches/%s/questions/" % batch_id)


@login_required
def check_name(request, survey_id):
    response = Batch.objects.filter(
        name=request.GET['name'], survey__id=survey_id).exists()
    return HttpResponse(json.dumps(not response), content_type="application/json")


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
