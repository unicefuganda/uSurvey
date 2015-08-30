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
from survey.forms.filters import QuestionFilterForm,  MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE, DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE
from survey.models import Question, Batch, QuestionTemplate, QuestionFlow, TextArgument
from survey.forms.question import QuestionForm #, QuestionFlowForm
from survey.utils.query_helper import get_filterset
from survey.views.custom_decorators import not_allowed_when_batch_is_open
from survey.forms.logic import LogicForm
from django.conf import settings


ADD_LOGIC_ON_OPEN_BATCH_ERROR_MESSAGE = "Logics cannot be added while the batch is open."
ADD_SUBQUESTION_ON_OPEN_BATCH_ERROR_MESSAGE = "Subquestions cannot be added while batch is open."
REMOVE_QUESTION_FROM_OPEN_BATCH_ERROR_MESSAGE = "Question cannot be removed from a batch while the batch is open."

def _max_number_of_question_per_page(number_sent_in_request):
    max_question_per_page_supplied = number_sent_in_request or 0
    given_max_per_page = min(int(max_question_per_page_supplied), MAX_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE)
    return max(given_max_per_page, DEFAULT_NUMBER_OF_QUESTION_DISPLAYED_PER_PAGE)

@permission_required('auth.can_view_batches')
def index(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    data = dict(request.GET)
    questions = batch.questions_inline()
    if data:
        question_filter_form = QuestionFilterForm(data=data, batch=batch)
        questions = batch.batch_questions.filter(pk__in=[q.pk for q in questions])
        questions = question_filter_form.filter(questions)
    else:
        question_filter_form = QuestionFilterForm(batch=batch)
    #question_library =  question_filter_form.filter(QuestionTemplate.objects.all())
    max_per_page = _max_number_of_question_per_page(data.get('number_of_questions_per_page', 0))
    question_form = QuestionForm(batch)

    if batch.start_question is None:
        messages.error(request, 'There are no questions associated with this batch yet.')
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
        (batch.survey.name, reverse('batch_index_page', args=(batch.survey.pk, ))),
    ])
    question_rules_for_batch = {}
    context = {'questions': questions, 'request': request, 'batch': batch, 'max_question_per_page':max_per_page,
               'question_filter_form': question_filter_form, 'rules_for_batch': question_rules_for_batch}
    return render(request, 'questions/index.html', context)

# @permission_required('auth.can_view_batches')
# @not_allowed_when_batch_is_open(message=ADD_SUBQUESTION_ON_OPEN_BATCH_ERROR_MESSAGE,
#                                 redirect_url_name="batch_questions_page", url_kwargs_keys=['batch_id'])
# def new_subquestion(request, question_id, batch_id=None):
#     parent_question = Question.objects.get(pk=question_id)
#     questionform = QuestionForm(parent_question=parent_question)
#     response = None
#     if request.method == 'POST':
#         questionform = QuestionForm(request.POST, parent_question=parent_question)
#         response = __process_sub_question_form(request, questionform, parent_question, 'added', batch_id)
#     context = {'questionform': questionform, 'button_label': 'Create', 'id': 'add-sub_question-form',
#                'cancel_url': reverse('batch_questions_page', args=(batch.pk, )), 'parent_question': parent_question, 'class': 'question-form',
#                'heading': 'Add SubQuestion'}
# 
#     template_name = 'questions/new.html'
#     if request.is_ajax():
#         template_name = 'questions/_add_question.html'
# 
#     return response or render(request, template_name, context)

@permission_required('auth.can_view_batches')
def edit_subquestion(request, question_id, batch_id=None):
    question = Question.objects.get(pk=question_id)
    questionform = QuestionForm(instance=question)
    response = None
    if request.method == 'POST':
        questionform = QuestionForm(request.POST, instance=question)
        response = __process_sub_question_form(request, questionform, question.parent, 'edited', batch_id)
    context = {'questionform': questionform, 'button_label': 'Save', 'id': 'add-sub_question-form',
               'cancel_url': reverse('batch_questions_page', args=(batch.pk, )), 'parent_question': question.parent, 'class': 'question-form',
               'heading': 'Edit Subquestion'}

    template_name = 'questions/new.html'

    return response or render(request, template_name, context)

@permission_required('auth.can_view_batches')
def delete(request, question_id, batch_id=None):
    question = Question.objects.filter(pk=question_id)
    redirect_url = '/batches/%s/questions/' % batch_id if batch_id else reverse('batch_questions_page', args=(batch.pk, ))
    if question:
        success_message = "%s successfully deleted."
        messages.success(request, success_message % ("Sub question" if question[0].subquestion else "Question"))
    else:
        messages.error(request, "Question / Subquestion does not exist.")
    question.delete()
    return HttpResponseRedirect(redirect_url)

@permission_required('auth.can_view_batches')
@not_allowed_when_batch_is_open(message=ADD_LOGIC_ON_OPEN_BATCH_ERROR_MESSAGE,
                                redirect_url_name="batch_questions_page", url_kwargs_keys=['batch_id'])
def add_logic(request, batch_id, question_id):
    question = Question.objects.get(id=question_id)
    batch = Batch.objects.get(id=batch_id)
    logic_form = LogicForm(question=question, batch=batch)
    response = None
    question_rules_for_batch = {}
#     question_rules_for_batch[question] = question.rules_for_batch(batch)
    if request.method == "POST":
        logic_form = LogicForm(data=request.POST, question=question, batch=batch)
        if logic_form.is_valid():
            pass
            messages.success(request, 'Logic successfully added.')
            response = HttpResponseRedirect('/batches/%s/questions/' % batch_id)

    context = {'logic_form': logic_form, 'button_label': 'Save', 'question': question,
               'rules_for_batch': question_rules_for_batch,
               'questionform': QuestionForm(parent_question=question, batch=batch),
               'modal_action': '/questions/%s/sub_questions/new/' % question.id,
               'class': 'question-form', 'batch_id': batch_id, 'batch': batch,
               'cancel_url': '/batches/%s/questions/' % batch_id}
    return response or render(request, "questions/logic.html", context)

@permission_required('auth.can_view_batches')
def edit(request, question_id):
    questions = Question.objects.filter(id=question_id)
    if not questions:
        messages.error(request, "Question does not exist.")
        return HttpResponseRedirect(reverse('batch_questions_page', args=(batch.pk, )))
    question = questions[0]
    response, context = _render_question_view(request, question.batch, question)
    return response or render(request, 'questions/new.html', context)

@permission_required('auth.can_view_batches')
def new(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    response, context = _render_question_view(request, batch)
    return response or render(request, 'questions/new.html', context)

def _process_question_form(request, batch, response, instance=None):
    question_form = QuestionForm(batch, data=request.POST, instance=instance)
    action_str = 'edit' if instance else 'add'
    if question_form.is_valid():
        question_form.save(**request.POST)
        messages.success(request, 'Question successfully %sed.' % action_str)
        response = HttpResponseRedirect(reverse('batch_questions_page', args=(batch.pk, )))
    else:
        messages.error(request, 'Question was not %sed.' % action_str)
#         options = dict(request.POST).get('options', None)
    return response, question_form


def _render_question_view(request, batch, instance=None):
    question_form = QuestionForm(batch, instance=instance)
    button_label = 'Create'
    options = None
    response = None
    if instance:
        button_label = 'Save'
        options = instance.options.all()
        options = [option.text for option in options] if options else None

    if request.method == 'POST':
        response, question_form = _process_question_form(request, batch, response, instance)

    context = {'button_label': button_label,
               'id': 'add-question-form',
               'request': request,
               'class': 'question-form',
               'cancel_url': reverse('batch_questions_page', args=(batch.pk, )),
               'questionform': question_form}

    if options:
        options = filter(lambda text: text.strip(), list(OrderedDict.fromkeys(options)))
        options = map(lambda option: re.sub("[%s]" % settings.USSD_IGNORED_CHARACTERS, '', option), options)
        context['options'] = map(lambda option: re.sub("  ", ' ', option), options)

    return response, context


@permission_required('auth.can_view_batches')
@not_allowed_when_batch_is_open(message=REMOVE_QUESTION_FROM_OPEN_BATCH_ERROR_MESSAGE,
                                redirect_url_name="batch_questions_page", url_kwargs_keys=['batch_id'])
def remove(request, batch_id, question_id):
    batch = Batch.objects.get(id=batch_id)
    get_object_or_404(Question, id=question_id, batch__id=batch_id).delete()
    messages.success(request, "Question successfully removed from %s." % batch.name)
    return HttpResponseRedirect('/batches/%s/questions/' % batch_id)

@permission_required('auth.can_view_batches')
def _index(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    data = dict(request.GET)
    question_filter_form = QuestionFilterForm(data=data, batch=batch)
    question_library =  question_filter_form.filter(QuestionTemplate.objects.all())
    question_form = QuestionForm(batch)
    question_flow_form = QuestionFlowForm()
    question_tree = None
    if batch.start_question:
        question_tree = batch.batch_questions.all()
#     import pdb; pdb.set_trace()
    context = {'batch': batch, 'batch_question_tree' : question_tree, 'question_form' : question_form, 'button_label' : 'Add',
               'id' : 'question_form', 'action': '#', 
               'question_library' : question_library, 'question_filter_form' : question_filter_form, 
               'question_flow_form' : question_flow_form}
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
                question.text=item['text']                                 
                question.answer_type=item['answer_type']     
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
                #import pdb; pdb.set_trace()
                f, _ = QuestionFlow.objects.get_or_create(question=nodes[source_identifier], 
                                                   next_question=nodes[flow['target']],
                                                   validation_test=flow['validation_test']
                                               )
                ##now create test arguments
                for idx, arg in enumerate(flow['validation_arg']):
                    if arg.strip():
                        TextArgument.objects.get_or_create(flow=f, position=idx, param=arg)
        #remove strayed questions
        batch.batch_questions.exclude(identifier__in=nodes.keys()).delete()
    return HttpResponseRedirect(reverse('batch_questions_page', args=(batch_id)))

def export_all_questions(request):
    pass

def export_batch_questions(request):
    pass

