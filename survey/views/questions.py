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
from survey.services.export_questions import get_question_template_as_dump
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

@permission_required('auth.can_view_batches')
@not_allowed_when_batch_is_open(message=ADD_SUBQUESTION_ON_OPEN_BATCH_ERROR_MESSAGE,
                                redirect_url_name="batch_questions_page", url_kwargs_keys=['batch_id'])
def new_subquestion(request, batch_id):
    return _save_subquestion(request, batch_id)

def _save_subquestion(request, batch_id, instance=None):
    #possible subquestions are questions not bound to any interviewer yet
    batch = get_object_or_404(Batch, pk=batch_id)
    questionform = QuestionForm(batch, instance=instance)
    if request.method == 'POST':
        questionform = QuestionForm(batch, data=request.POST, instance=instance)
        if questionform.is_valid():
            if instance:
                zombify = False
            else:
                zombify = True
            question = questionform.save(zombie=zombify)
            if request.is_ajax():
                return HttpResponse(json.dumps({'id' : question.pk, 'text' : question.text}), mimetype='application/json')
            messages.info(request, 'Sub Question saved')
    if instance:
        heading = 'Edit Subquestion'
    else:
        heading = 'New Subquestion'
    context = {'questionform': questionform, 'button_label': 'Create', 'id': 'add-sub_question-form',
               'save_url' : reverse('add_batch_subquestion_page', args=(batch.pk, )),
               'cancel_url': reverse('batch_questions_page', args=(batch.pk, )), 'class': 'question-form',
               'heading': heading}
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
        (batch.survey.name, reverse('batch_index_page', args=(batch.survey.pk, ))),
        (batch.name, reverse('batch_questions_page', args=(batch.pk, ))),
    ])
    template_name = 'questions/new.html'
    if request.is_ajax():
        template_name = 'questions/_add_question.html'
        return render(request, template_name, context)
    else:
        return HttpResponseRedirect(reverse('batch_questions_page', args=(batch.pk, )))

def get_sub_questions_for_question(request, question_id):
    question = Question.objects.get(id=question_id)
    return _create_question_hash_response(Question.zombies(question.batch))

def get_questions_for_batch(request, batch_id, question_id):
    batch = Batch.objects.get(id=batch_id)
    questions = batch.questions_inline()
    questions = [q for q in questions if int(q.pk) is not int(question_id)]
    return _create_question_hash_response(questions)

def _create_question_hash_response(questions):
    questions_to_display = map(lambda question: {'id': str(question.id), 'text': question.text}, questions)
    return HttpResponse(json.dumps(questions_to_display), mimetype='application/json')

@permission_required('auth.can_view_batches')
def edit_subquestion(request, question_id, batch_id=None):
    question = Question.objects.get(pk=question_id)
    return _save_subquestion(request, batch_id, instance=question)

@permission_required('auth.can_view_batches')
def delete(request, question_id, batch_id=None):
    question = get_object_or_404(Question, pk=question_id)
    batch = question.batch
    redirect_url = '/batches/%s/questions/' % batch_id if batch_id else reverse('batch_questions_page', args=(batch.pk, ))
    if question:
        success_message = "Question successfully deleted."
        messages.success(request, success_message) #% ("Sub question" if question.subquestion else "Question"))
    else:
        messages.error(request, "Question / Subquestion does not exist.")
    next_question = batch.next_inline(question)
    previous_inline = question.connecting_flows.filter(validation_test__isnull=True)
    if previous_inline:
        QuestionFlow.objects.create(question=previous_inline[0], next_question=next_question)
    else:
        batch.start_question = next_question
        batch.save()
    question.delete()
    return HttpResponseRedirect(redirect_url)

@permission_required('auth.can_view_batches')
@not_allowed_when_batch_is_open(message=ADD_LOGIC_ON_OPEN_BATCH_ERROR_MESSAGE,
                                redirect_url_name="batch_questions_page", url_kwargs_keys=['batch_id'])
def add_logic(request, batch_id, question_id):
    question = Question.objects.get(id=question_id)
    batch = Batch.objects.get(id=batch_id)
    response = None
    logic_form = LogicForm(question=question)
    question_rules_for_batch = {}
#     question_rules_for_batch[question] = question.rules_for_batch(batch)
    if request.method == "POST":
        logic_form = LogicForm(data=request.POST, question=question)
        if logic_form.is_valid():
            logic_form.save()
            messages.success(request, 'Logic successfully added.')
            response = HttpResponseRedirect('/batches/%s/questions/' % batch_id)
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
        (batch.survey.name, reverse('batch_index_page', args=(batch.survey.pk, ))),
        (batch.name, reverse('batch_questions_page', args=(batch.pk, ))),
    ])

    context = {'logic_form': logic_form, 'button_label': 'Save', 'question': question,
               'rules_for_batch': question_rules_for_batch,
               'questionform': QuestionForm(parent_question=question, batch=batch),
               'modal_action': reverse('add_batch_subquestion_page', args=(batch.pk, )),
               'class': 'question-form', 'batch_id': batch_id, 'batch': batch,
               'cancel_url': '/batches/%s/questions/' % batch_id}
    return response or render(request, "questions/logic.html", context)

@permission_required('auth.can_view_batches')
def delete_logic(request, batch_id, flow_id):
    flow = QuestionFlow.objects.get(id=flow_id)
    flow.delete()
    messages.success(request, "Logic successfully deleted.")
    return HttpResponseRedirect('/batches/%s/questions/' % batch_id)

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
    request.breadcrumbs([
        ('Surveys', reverse('survey_list_page')),
        (batch.survey.name, reverse('batch_index_page', args=(batch.survey.pk, ))),
        (batch.name, reverse('batch_questions_page', args=(batch.pk, ))),
    ])
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

def export_batch_questions(request, batch_id):
    batch = Batch.objects.get(pk=batch_id)
    filename =  '%s_questions' % batch.name
    formatted_responses = get_question_template_as_dump(batch.survey_questions())
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    response.write("\r\n".join(formatted_responses))
    return response
