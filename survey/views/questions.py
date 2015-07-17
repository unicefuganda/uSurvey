import json
import re
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import permission_required
from survey.forms.filters import QuestionFilterForm
from survey.models import Question, Batch, QuestionTemplate, QuestionFlow, TextArgument
from survey.forms.question import QuestionForm, QuestionFlowForm
from survey.utils.query_helper import get_filterset


ADD_LOGIC_ON_OPEN_BATCH_ERROR_MESSAGE = "Logics cannot be added while the batch is open."
ADD_SUBQUESTION_ON_OPEN_BATCH_ERROR_MESSAGE = "Subquestions cannot be added while batch is open."
REMOVE_QUESTION_FROM_OPEN_BATCH_ERROR_MESSAGE = "Question cannot be removed from a batch while the batch is open."


@permission_required('auth.can_view_batches')
def index(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    data = dict(request.GET)
    data['groups'] = batch.group.id
    question_filter_form = QuestionFilterForm(data=data, read_only=['groups'], batch=batch)
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
        if batch.start_question: 
            batch.start_question.delete()
        data = request.POST.get('questions_data')
        question_graph = json.loads(data)
        nodes = {}
        connections = {}
        targets = []
        for item in question_graph:
            if item.get('identifier', False):
                nodes[item['identifier']], _ = Question.objects.get_or_create(identifier=item['identifier'], 
                                                                           text=item['text'], 
                                                                           answer_type=item['answer_type'],
                                                                           batch=batch
                                                                           )
            if item.get('source', False):
                targets.append(item['target'].strip('q_'))
                source_identifier = item['source'].strip('q_')
                flows = connections.get(source_identifier, [])
                flows.append(item)
                connections[source_identifier] = flows
        for source_identifier, flows in connections.items():
            for flow in flows:
                #import pdb; pdb.set_trace()
                f, _ = QuestionFlow.objects.get_or_create(question=nodes[source_identifier], 
                                                   next_question=nodes[flow['target'].strip('q_')],
                                                   validation_test=flow['validation_test']
                                               )
                ##now create test arguments
                for idx, arg in enumerate(flow['validation_arg']):
                    if arg.strip():
                        TextArgument.objects.get_or_create(flow=f, position=idx, param=arg)
        source_question_ids = connections.keys()
        root_question_id = set(source_question_ids).difference(targets).pop()
#         import pdb; pdb.set_trace()
        batch.start_question = nodes[root_question_id]
        batch.save()
    return HttpResponse(data);

def export_all_questions(request):
    pass

def export_batch_questions(request):
    pass

