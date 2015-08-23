import json
import re
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import permission_required
from survey.forms.filters import QuestionFilterForm
from survey.models import QuestionTemplate
from survey.forms.question_template import QuestionTemplateForm
from survey.services.export_questions import get_question_template_as_dump
from survey.utils.query_helper import get_filterset
from django.core.urlresolvers import reverse

@permission_required('auth.can_view_batches')
def index(request):
    '''
        show all library questions
    '''
    question_filter_form = QuestionFilterForm(data=request.GET)
    questions =  question_filter_form.filter(QuestionTemplate.objects.all())
    search_fields = ['identifier', 'group__name', 'text', ]
    if request.GET.has_key('q'):
        questions = get_filterset(questions, request.GET['q'], search_fields)
    context = {'questions': questions, 'request': request, 'question_filter_form' : question_filter_form}
    return render(request, 'question_templates/index.html', context)

@permission_required('auth.can_view_batches')
def filter(request):
    question_lib = QuestionTemplate.objects.all()
    search_fields = ['identifier', 'text', ]
    if request.GET.has_key('q'):
        question_lib = get_filterset(question_lib, request.GET['q'], search_fields)
    question_filter_form = QuestionFilterForm(data=request.GET)
    questions =  question_filter_form.filter(question_lib).values('id', 'text', 'answer_type', 'group', 'module').order_by('text')
    json_dump = json.dumps(list(questions), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')

def _process_question_form(request, response, instance=None):
    question_form = QuestionTemplateForm(data=request.POST, instance=instance)
    action_str = 'edit' if instance else 'add'
    if question_form.is_valid():
        question_form.save()
        messages.success(request, 'Question successfully %sed.' % action_str)
        response = HttpResponseRedirect(reverse('show_question_library'))
    else:
        messages.error(request, 'Question was not %sed.' % action_str)
    return response, question_form

def _render_question_view(request, instance=None):
    question_form = QuestionTemplateForm(instance=instance)
    button_label = 'Create'
    options = None
    response = None
    if instance:
        button_label = 'Save'

    if request.method == 'POST':
        response, question_form = _process_question_form(request, response, instance)
    request.breadcrumbs([
        ('Question Library', reverse('show_question_library')),
    ])
    context = {'button_label': button_label,
               'id': 'add-question-form',
               'request': request,
               'class': 'question-form',
               'cancel_url': reverse('show_question_library'),
               'questionform': question_form}
    return response, context

@permission_required('auth.can_view_batches')
def add(request):
    '''
        create all library questions
    '''
    response, context = _render_question_view(request)
    return response or render(request, 'question_templates/new.html', context)

@permission_required('auth.can_view_batches')
def edit(request, question_id):
    '''
        Modify library question
    '''
    question = get_object_or_404(QuestionTemplate, pk=question_id)
    response, context = _render_question_view(request, instance=question)
    return response or render(request, 'question_templates/new.html', context)

@permission_required('auth.can_view_batches')
def delete(request, question_id):
    '''
        Delete library question
    '''
    try:
        question = get_object_or_404(QuestionTemplate, pk=question_id)
        identifier = question.identifier
        question.delete()
        messages.success(request, 'Question Deleted question %s.' % identifier)
    except Exception:
        messages.error(request, 'Unable to delete question %s.' % identifier)
    return HttpResponseRedirect(reverse('show_question_library'))
    

def export_questions(request):
    filename =  'library_questions'
    formatted_responses = get_question_template_as_dump()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    response.write("\r\n".join(formatted_responses))
    return response

