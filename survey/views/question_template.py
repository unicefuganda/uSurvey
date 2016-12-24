import json
import re
from collections import OrderedDict
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import permission_required
from survey.forms.filters import QuestionFilterForm
from survey.models import QuestionTemplate, ParameterTemplate, TemplateQuestion
from survey.forms.question_template import get_question_templates_form
from survey.services.export_questions import get_question_template_as_dump
from survey.utils.query_helper import get_filterset
from django.core.urlresolvers import reverse
from django.conf import settings


@permission_required('auth.can_view_batches')
def index(request, model_class=QuestionTemplate):
    '''
        show all library questions
    '''
    question_filter_form = QuestionFilterForm(data=request.GET or None)
    questions = question_filter_form.filter(model_class.objects.all())
    search_fields = ['identifier', 'text', ]
    if request.GET.has_key('q'):
        questions = get_filterset(questions, request.GET['q'], search_fields)
    context = {'questions': questions, 'request': request,
               'placeholder': 'identifier, text',
               'question_filter_form': question_filter_form, 'model_class': model_class}
    if model_class == ParameterTemplate:
        request.breadcrumbs([
            ('Groups', reverse('respondent_groups_page')),
        ])
    return render(request, 'question_templates/index.html', context)


@permission_required('auth.can_view_batches')
def filter(request):
    question_lib = QuestionTemplate.objects.all()
    search_fields = ['identifier', 'text', ]
    if request.GET.has_key('q'):
        question_lib = get_filterset(
            question_lib, request.GET['q'], search_fields)
    question_filter_form = QuestionFilterForm(data=request.GET)
    questions = question_filter_form.filter(question_lib).values(
        'id', 'text', 'answer_type', 'module').order_by('text')
    json_dump = json.dumps(list(questions), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')


def _process_question_form(request, response, model_class, instance=None):
    QuestionTemplateForm = get_question_templates_form(model_class)
    question_form = QuestionTemplateForm(data=request.POST, instance=instance)
    action_str = 'edit' if instance else 'add'
    if question_form.is_valid():
        question_form.save()
        messages.success(request, 'Question successfully %sed.' % action_str)
        if request.POST.has_key('add_more_button'):
            redirect_age = ''
        else:
            redirect_age = reverse('show_%s' % model_class.resolve_tag())
        response = HttpResponseRedirect(redirect_age)
    else:
        messages.error(request, 'Question was not %sed.' % action_str)
    return response, question_form


def _render_question_view(request, model_class, instance=None):
    QuestionTemplateForm = get_question_templates_form(model_class)
    question_form = QuestionTemplateForm(instance=instance)
    button_label = 'Create'
    options = None
    response = None
    if instance:
        button_label = 'Save'
        options = instance.options.all().order_by('order')
        # options = [option.text for option in options] if options else None
    if request.method == 'POST':
        response, question_form = _process_question_form(
            request, response, model_class, instance)
    request.breadcrumbs([
        (model_class.verbose_name(), reverse('show_%s' % model_class.resolve_tag())),
    ])
    context = {'button_label': button_label,
               'id': 'add-question-form',
               'request': request,
               'class': 'question-form',
               'cancel_url': reverse('show_%s' % model_class.resolve_tag()),
               'questionform': question_form,
               'model_class': model_class}

    if options:
        #options = map(lambda option: re.sub("[%s]" % settings.USSD_IGNORED_CHARACTERS, '', option), options)
        # map(lambda option: re.sub("  ", ' ', option), options)
        context['options'] = options
    return response, context


@permission_required('auth.can_view_batches')
def add(request, model_class=QuestionTemplate):
    '''
        create all library questions
    '''
    response, context = _render_question_view(request, model_class)
    return response or render(request, 'question_templates/new.html', context)


@permission_required('auth.can_view_batches')
def edit(request, question_id):
    '''
        Modify library question
    '''
    try:
        question = TemplateQuestion.get(pk=question_id)
    except TemplateQuestion.DoesNotExist:
        return HttpResponseNotFound()
    response, context = _render_question_view(request, model_class=question.__class__, instance=question)
    return response or render(request, 'question_templates/new.html', context)


@permission_required('auth.can_view_batches')
def delete(request, question_id):
    '''
        Delete library question
    '''
    try:
        try:
            question = TemplateQuestion.get(pk=question_id)
            model_class = question.__class__
        except TemplateQuestion.DoesNotExist:
            return HttpResponseNotFound()
        identifier = question.identifier
        question.delete()
        messages.success(request, 'Question Deleted question %s.' % identifier)
    except Exception:
        messages.error(request, 'Unable to delete question %s.' % identifier)
    return HttpResponseRedirect(reverse('show_%s' % model_class.resolve_tag()))


def export_questions(request, model_class=QuestionTemplate):
    filename = '%ss' % model_class.verbose_name()
    questions = model_class.objects.all()
    formatted_responses = get_question_template_as_dump(questions)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    response.write("\r\n".join(formatted_responses))
    return response
