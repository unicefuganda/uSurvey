import json
import re
from django.core.urlresolvers import reverse
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

