import json
import re
from collections import OrderedDict
from django.core.urlresolvers import reverse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from survey.forms.filters import QuestionFilterForm,  \
    MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE, DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE
from survey.models import Question, QuestionSet
from survey.models import Batch, QuestionTemplate, QuestionFlow, TextArgument, TemplateOption, QuestionSet
from survey.models import QuestionModule, QuestionOption
from survey.forms.question import get_question_form  # , QuestionFlowForm
from survey.forms.batch import BatchQuestionsForm
from survey.services.export_questions import get_batch_question_as_dump
from survey.utils.query_helper import get_filterset
from survey.views.custom_decorators import not_allowed_when_batch_is_open
from survey.forms.logic import LogicForm, LoopingForm


ADD_LOGIC_ON_OPEN_BATCH_ERROR_MESSAGE = "Logics cannot be added while the batch is open."
ADD_SUBQUESTION_ON_OPEN_BATCH_ERROR_MESSAGE = "Subquestions cannot be added while batch is open."
REMOVE_QUESTION_FROM_OPEN_BATCH_ERROR_MESSAGE = "Question cannot be removed from a batch while the batch is open."


def _max_number_of_question_per_page(number_sent_in_request):
    max_question_per_page_supplied = number_sent_in_request or 0
    given_max_per_page = min(
        int(max_question_per_page_supplied), MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE)
    return max(given_max_per_page, DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE)


QuestionForm = get_question_form(Question)


@permission_required('auth.can_view_batches')
def index(request, qset_id):
    # now I'm gonna call question set a batch of questions. If there's time, I'll rename them properly
    # So don't get confused :)
    batch = QuestionSet.get(pk=qset_id)
    questions = batch.questions_inline()
    max_per_page = None
    if request.method == 'GET':
        question_filter_form = QuestionFilterForm(
            data=request.GET, qset=batch)
        batch_questions = batch.questions.all()
        search_fields = ['identifier',  'text', ]
        if request.GET.has_key('q'):
            questions = get_filterset(
                batch_questions, request.GET['q'], search_fields)
        relevant_questions = question_filter_form.filter(batch_questions)
        questions = [q for q in questions if q in relevant_questions]
        # now maintain same inline other exclusing questions in
        max_per_page = _max_number_of_question_per_page(
            request.GET.get('number_of_questions_per_page', 0))
    else:
        question_filter_form = QuestionFilterForm(qset=batch)
    #question_library =  question_filter_form.filter(QuestionTemplate.objects.all())
    question_form = QuestionForm(batch)

    request.breadcrumbs([
        (batch.verbose_name(), reverse('%s_home' % batch.resolve_tag()), ),
    ])
    context = {'questions': questions, 'request': request, 'batch': batch, 'max_question_per_page': max_per_page,
               'question_filter_form': question_filter_form,
               'placeholder': 'identifier, text',
               }
    return render(request, 'set_questions/index.html', context)


@permission_required('auth.can_view_batches')
@not_allowed_when_batch_is_open(message=ADD_SUBQUESTION_ON_OPEN_BATCH_ERROR_MESSAGE,
                                redirect_url_name="batch_questions_page", url_kwargs_keys=['batch_id'])
def new_subquestion(request, batch_id):
    return _save_subquestion(request, batch_id)


def _save_subquestion(request, batch_id, instance=None):
    # possible subquestions are questions not bound to any interviewer yet
    batch = QuestionSet.get(pk=batch_id)
    questionform = QuestionForm(batch, instance=instance)
    if request.method == 'POST':
        questionform = QuestionForm(
            batch, data=request.POST, instance=instance)
        if questionform.is_valid():
            if instance:
                zombify = False
            else:
                zombify = True
            question = questionform.save(zombie=zombify)
            if request.is_ajax():
                return HttpResponse(json.dumps({'id': question.pk, 'text': question.text,
                                                'identifier': question.identifier}), content_type='application/json')
            messages.info(request, 'Sub Question saved')
    if instance:
        heading = 'Edit Subquestion'
    else:
        heading = 'New Subquestion'
    context = {'questionform': questionform, 'button_label': 'Create', 'id': 'add-sub_question-form',
               'save_url': reverse('%s_home' % batch.resolve_tag()),
               'cancel_url': reverse('qset_questions_page', args=(batch.pk, )), 'class': 'question-form',
               'heading': heading}
    request.breadcrumbs([
        (batch.verbose_name(), reverse('%s_home' % batch.resolve_tag()), ),
        (batch.name, reverse('qset_questions_page', args=(batch.pk, ))),
    ])
    template_name = 'set_questions/new.html'
    if request.is_ajax():
        template_name = 'set_questions/_add_question.html'
        return render(request, template_name, context)
    else:
        return HttpResponseRedirect(reverse('qset_questions_page', args=(batch.pk, )))


def get_sub_questions_for_question(request, question_id):
    question = Question.objects.get(id=question_id)
    return _create_question_hash_response(Question.zombies(question.batch))


def get_prev_questions_for_question(request, question_id):
    question = Question.objects.get(id=question_id)
    return _create_question_hash_response(question.previous_inlines())


def get_questions_for_batch(request, batch_id, question_id):
    batch = QuestionSet.get(id=batch_id)
    questions = batch.questions_inline()
    questions = [q for q in questions if int(q.pk) is not int(question_id)]
    return _create_question_hash_response(questions)


def _create_question_hash_response(questions):
    questions_to_display = map(lambda question: {'id': str(
        question.id), 'text': question.text, 'identifier': question.identifier}, questions)
    return HttpResponse(json.dumps(questions_to_display), content_type='application/json')


@permission_required('auth.can_view_batches')
def edit_subquestion(request, question_id, batch_id=None):
    question = Question.objects.get(pk=question_id)
    return _save_subquestion(request, batch_id, instance=question)


@permission_required('auth.can_view_batches')
def delete(request, question_id, batch_id=None):
    return _remove(request, batch_id, question_id)


@permission_required('auth.can_view_batches')
def add_logic(request, qset_id, question_id):
    question = Question.get(id=question_id)
    batch = QuestionSet.get(id=qset_id)
    response = None
    logic_form = LogicForm(question)
    question_rules_for_batch = {}
#     question_rules_for_batch[question] = question.rules_for_batch(batch)
    if request.method == "POST":
        logic_form = LogicForm(question, data=request.POST)
        if logic_form.is_valid():
            logic_form.save()
            messages.success(request, 'Logic successfully added.')
            response = HttpResponseRedirect(reverse('qset_questions_page', args=(batch.pk, )))
    request.breadcrumbs([
        (batch.verbose_name(), reverse('%s_home' % batch.resolve_tag()), ),
        (batch.name, reverse('qset_questions_page', args=(batch.pk, ))),
    ])
    context = {'logic_form': logic_form, 'button_label': 'Save', 'question': question,
               'rules_for_batch': question_rules_for_batch,
               'questionform': QuestionForm(batch, parent_question=question),
               'modal_action': reverse('add_qset_subquestion_page', args=(batch.pk, )),
               'class': 'question-form', 'batch_id': qset_id, 'batch': batch,
               'cancel_url': reverse('%s_home' % batch.resolve_tag())}
    return response or render(request, "set_questions/logic.html", context)


# def start_loop(request, question_id):
#     question = Question.get(id=question_id)
#     response = None
#     looping_form = LoopingForm(question)
#     if request.method == "POST":
#         logic_form = LoopingForm(question, data=request.POST)
#         if logic_form.is_valid():
#             logic_form.save()
#             messages.success(request, 'Logic successfully added.')
#             response = HttpResponseRedirect(reverse('qset_questions_page', args=(batch.pk, )))
#     request.breadcrumbs([
#         (batch.verbose_name(), reverse('%s_home' % batch.resolve_tag()), ),
#         (batch.name, reverse('qset_questions_page', args=(batch.pk, ))),
#     ])
#     context = {'logic_form': logic_form, 'button_label': 'Save', 'question': question,
#                'rules_for_batch': question_rules_for_batch,
#                'questionform': QuestionForm(batch, parent_question=question),
#                'modal_action': reverse('add_qset_subquestion_page', args=(batch.pk, )),
#                'class': 'question-form', 'batch_id': qset_id, 'batch': batch,
#                'cancel_url': reverse('%s_home' % batch.resolve_tag())}
#     return response or render(request, "set_questions/logic.html", context)


@permission_required('auth.can_view_batches')
def delete_logic(request, flow_id):
    flow = QuestionFlow.objects.get(id=flow_id)
    batch = flow.question.qset
    flow.delete()
    _kill_zombies(batch.zombie_questions())
    messages.success(request, "Logic successfully deleted.")
    return HttpResponseRedirect(reverse('qset_questions_page', args=(batch.pk, )))


@permission_required('auth.can_view_batches')
def edit(request, question_id):
    questions = Question.objects.filter(id=question_id)
    if not questions:
        messages.error(request, "Question does not exist.")
        return HttpResponseRedirect(reverse('survey_list_page'))
    question = questions[0]
    response, context = _render_question_view(
        request, QuestionSet.objects.get_subclass(pk=question.qset.pk), question)
    return response or render(request, 'set_questions/new.html', context)


@permission_required('auth.can_view_batches')
def new(request, qset_id):
    batch = QuestionSet.get(pk=qset_id)
    response, context = _render_question_view(request, batch)
    return response or render(request, 'set_questions/new.html', context)


@permission_required('auth.can_view_batches')
def insert(request, prev_quest_id):
    prev_question = Question.get(pk=prev_quest_id)
    batch = QuestionSet.get(pk=prev_question.qset.pk)
    response, context = _render_question_view(request, batch, prev_question=prev_question)
    return response or render(request, 'set_questions/new.html', context)


def _process_question_form(request, batch, response, question_form):
    instance = question_form.instance
    action_str = 'edit' if instance else 'add'
    if question_form.is_valid():
        question = question_form.save(**request.POST)
        if request.POST.has_key('add_to_lib_button'):
            qt = QuestionTemplate.objects.create(identifier=question.identifier,
                                                 group=question.group,
                                                 text=question.text,
                                                 answer_type=question.answer_type,
                                                 module=question.module)
            options = question.options.all()
            if options:
                topts = []
                for option in options:
                    topts.append(TemplateOption(
                        question=qt, text=option.text, order=option.order))
                TemplateOption.objects.bulk_create(topts)
            messages.success(
                request, 'Question successfully %sed. to library' % action_str)
        messages.success(request, 'Question successfully %sed.' % action_str)
        response = HttpResponseRedirect(
            reverse('qset_questions_page', args=(batch.pk, )))
    else:
        messages.error(request, 'Question was not %sed.' % action_str)
#         options = dict(request.POST).get('options', None)
    return response, question_form


def _render_question_view(request, batch, instance=None, prev_question=None):
    if prev_question is None:
        prev_question = batch.last_question_inline()
    button_label = 'Create'
    options = None
    response = None
    if instance:
        button_label = 'Save'
        options = instance.options.all().order_by('order')
        # options = [option.text.strip() for option in options] if options else None
    if request.method == 'POST':
        question_form = QuestionForm(batch, data=request.POST, instance=instance, prev_question=prev_question)
        response, question_form = _process_question_form(
            request, batch, response, question_form)
    else:
        question_form = QuestionForm(batch, instance=instance, prev_question=prev_question)
    context = {'button_label': button_label,
               'id': 'add-question-form',
               'request': request,
               'class': 'question-form',
               # 'prev_question': prev_question,
               'cancel_url': reverse('qset_questions_page', args=(batch.pk, )),
               'questionform': question_form}

    if options:
        #options = filter(lambda text: text.strip(), list(OrderedDict.fromkeys(options)))
        # options = map(lambda option: re.sub("[%s]" % settings.USSD_IGNORED_CHARACTERS, '', option), options)
        # map(lambda option: re.sub("  ", ' ', option), options)
        context['options'] = options
    request.breadcrumbs([
        (batch.verbose_name(), reverse('%s_home' % batch.resolve_tag()), ),
        (batch.name, reverse('qset_questions_page',  args=(batch.pk, )))
    ])
    return response, context

@permission_required('auth.can_view_batches')
def assign(request, qset_id):
    batch = QuestionSet.get(id=qset_id)
    if batch.interviews.count():
        error_message = "Questions cannot be assigned interviews has already been conducted: %s." % \
                        batch.name.capitalize()
        messages.error(request, error_message)
        return HttpResponseRedirect(reverse('qset_questions_page', args=(batch.pk, )))
    if request.method == 'POST':
        data = dict(request.POST)
        last_question = batch.last_question_inline()
        lib_questions = QuestionTemplate.objects.filter(
            identifier__in=data.get('identifier', ''))
        # qset_class =
        # print 'data: ', data, 'lib questions: ', lib_questions
        if lib_questions:
            for lib_question in lib_questions:
                question = Question.objects.create(identifier=lib_question.identifier,
                                                   text=lib_question.text,
                                                   answer_type=lib_question.answer_type,
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
        success_message = "Questions successfully assigned to %s: %s." % (batch.verbose_name(), batch.name.capitalize())
        messages.success(request, success_message)
        return HttpResponseRedirect(reverse('qset_questions_page', args=(batch.pk, )))
    used_identifiers = [
        question.identifier for question in batch.questions.all()]
    library_questions = QuestionTemplate.objects.exclude(
        identifier__in=used_identifiers).order_by('identifier')
    question_filter_form = QuestionFilterForm()
#     library_questions =  question_filter_form.filter(library_questions)
    request.breadcrumbs([
        (batch.verbose_name(), reverse('%s_home' % batch.resolve_tag()), ),
        (batch.name, reverse('qset_questions_page',  args=(batch.pk, )))
    ])
    context = {'batch_questions_form': unicode(BatchQuestionsForm()), 'batch': batch,
               'button_label': 'Save', 'id': 'assign-question-to-batch-form',
               'library_questions': library_questions, 'question_filter_form': question_filter_form}
    return render(request, 'set_questions/assign.html',
                  context)


@permission_required('auth.can_view_batches')
def update_orders(request, qset_id):
    batch = QuestionSet.get(id=qset_id)
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
    return HttpResponseRedirect(reverse('qset_questions_page',  args=(batch.pk, )))


@permission_required('auth.can_view_batches')
@not_allowed_when_batch_is_open(message=REMOVE_QUESTION_FROM_OPEN_BATCH_ERROR_MESSAGE,
                                redirect_url_name="batch_questions_page", url_kwargs_keys=['batch_id'])
def remove(request, batch_id, question_id):
    return _remove(request, batch_id, question_id)


def _kill_zombies(zombies):
    for z in zombies:
        z.delete()


def _remove(request, batch_id, question_id):
    question = Question.get(pk=question_id)
    batch = QuestionSet.get(pk=batch_id)
    redirect_url = reverse('qset_questions_page', args=(batch_id, ))
    if question.total_answers() > 0:
        messages.error(
            request, "Cannot delete question that has been answered at least once.")
    else:
        _kill_zombies(batch.zombie_questions())
        if question:
            success_message = "Question successfully deleted."
            # % ("Sub question" if question.subquestion else "Question"))
            messages.success(request, success_message)
        next_question = batch.next_inline(question)
        previous_inline = question.connecting_flows.filter(
            validation_test__isnull=True)
        if previous_inline.exists() and next_question:
            QuestionFlow.objects.create(question=previous_inline[
                                        0].question, next_question=next_question)
        elif next_question:
            # need to delete the previous flow for the next question
            batch.start_question = next_question
            batch.save()
        question.connecting_flows.all().delete()
        question.flows.all().delete()
        question.delete()
    return HttpResponseRedirect(redirect_url)


@permission_required('auth.can_view_batches')
def _index(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    data = dict(request.GET)
    question_filter_form = QuestionFilterForm(data=data, batch=batch)
    question_library = question_filter_form.filter(
        QuestionTemplate.objects.all())
    question_form = QuestionForm(batch)
    question_flow_form = None  # QuestionFlowForm()
    question_tree = None
    if batch.start_question:
        question_tree = batch.batch_questions.all()
    context = {'batch': batch, 'batch_question_tree': question_tree, 'question_form': question_form, 'button_label': 'Add',
               'id': 'question_form', 'action': '#',
               'question_library': question_library, 'question_filter_form': question_filter_form,
               'question_flow_form': question_flow_form}
    return render(request, 'questions/batch_question.html', context)


def submit(request, batch_id):
    if request.method == 'POST':
        batch = get_object_or_404(Batch, pk=batch_id)
        data = request.POST.get('questions_data')
        question_graph = json.loads(data)
        nodes = {}
        connections = {}
        targets = []
        root_question = None
        for item in question_graph:
            if item.get('identifier', False):
                question, _ = Question.objects.get_or_create(identifier=item['identifier'],
                                                             batch=batch)
                question.text = item['text']
                question.answer_type = item['answer_type']
                question.save()
                nodes[item['identifier']] = question
                if int(item.get('level', -1)) == 0:
                    batch.start_question = question
                    batch.save()
            if item.get('source', False):
                source_identifier = item['source']
                flows = connections.get(source_identifier, [])
                flows.append(item)
                connections[source_identifier] = flows
        for source_identifier, flows in connections.items():
            for flow in flows:
                f, _ = QuestionFlow.objects.get_or_create(question=nodes[source_identifier],
                                                          next_question=nodes[
                                                              flow['target']],
                                                          validation_test=flow[
                                                              'validation_test']
                                                          )
                # now create test arguments
                for idx, arg in enumerate(flow['validation_arg']):
                    if arg.strip():
                        TextArgument.objects.get_or_create(
                            flow=f, position=idx, param=arg)
        # remove strayed questions
        batch.batch_questions.exclude(identifier__in=nodes.keys()).delete()
    return HttpResponseRedirect(reverse('batch_questions_page', args=(batch_id)))


def export_all_questions(request):
    pass


def export_batch_questions(request, qset_id):
    batch = QuestionSet.get(pk=qset_id)
    filename = '%s_questions' % batch.name
    formatted_responses = get_batch_question_as_dump(batch.flow_questions)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    response.write("\r\n".join(formatted_responses))
    return response


