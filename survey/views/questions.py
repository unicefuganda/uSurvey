import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.contrib import messages

from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import permission_required
from survey.forms.logic import LogicForm
from survey.models import AnswerRule

from survey.models.batch import Batch
from survey.models.question import Question, QuestionOption
from survey.models.householdgroups import HouseholdMemberGroup

from survey.forms.question import QuestionForm


@permission_required('auth.can_view_batches')
def index(request, batch_id):
    batch = Batch.objects.get(id=batch_id)

    group_id = request.GET.get('group_id', None)

    if group_id and group_id != 'all':
        questions = HouseholdMemberGroup.objects.get(id=group_id).all_questions()
    else:
        questions = Question.objects.filter(batch=batch)

    if not questions.exists():
        messages.error(request, 'There are no questions associated with this batch yet.')
    context = {'questions': questions.filter(subquestion=False), 'request': request, 'batch': batch}
    return render(request, 'questions/index.html', context)

@permission_required('auth.can_view_batches')
def filter_by_group(request, batch_id, group_id):
    if group_id.lower() != 'all':
        questions = Question.objects.filter(group__id=group_id)
    else:
        questions = Question.objects.filter()
    questions_from_batch = Question.objects.filter(batch__id=batch_id)
    questions = questions.exclude(id__in=questions_from_batch).values('id', 'text').order_by('text')
    json_dump = json.dumps(list(questions), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')


@permission_required('auth.can_view_batches')
def list_all_questions(request):
    questions = Question.objects.filter(subquestion=False)
    context = {'questions': questions, 'request': request}
    return render(request, 'questions/index.html', context)


def __process_sub_question_form(request, questionform, parent_question):
    if questionform.is_valid():
        sub_question = questionform.save(commit=False)
        sub_question.subquestion = True
        sub_question.parent = parent_question
        sub_question.group = parent_question.group
        sub_question.save()
        messages.success(request, 'Sub question successfully added.')
        return HttpResponseRedirect('/questions/')


@permission_required('auth.can_view_batches')
def new_subquestion(request, question_id):
    parent_question = Question.objects.get(pk=question_id)
    questionform = QuestionForm()
    response = None
    if request.method == 'POST':
        questionform = QuestionForm(request.POST)
        response = __process_sub_question_form(request, questionform, parent_question)
    context = {'questionform': questionform, 'button_label': 'Save', 'id': 'add-sub_question-form', 'parent_question':parent_question}
    return response or render(request, 'questions/new.html', context)


def _get_post_values(post_data):
    next_question_key = post_data.get('next_question', None)
    option_key = post_data.get('option', None)
    question_key = post_data.get('validate_with_question', None)
    condition_response = post_data.get('condition', None)
    save_data = {'action': post_data['action'],
                 'condition': condition_response if condition_response else 'EQUALS_OPTION',
                 'next_question': Question.objects.get(id=next_question_key) if next_question_key else None,
                 'validate_with_value': post_data.get('value', None),
                 'validate_with_option': QuestionOption.objects.get(id=option_key) if option_key else None,
                 'validate_with_question': Question.objects.get(id=question_key) if question_key else None
                 }
    return save_data


@permission_required('auth.can_view_batches')
def add_logic(request, question_id):
    question = Question.objects.get(id=question_id)
    logic_form = LogicForm(question=question)
    if request.method == "POST":
        logic_form = LogicForm(data=request.POST, question=question)
        if logic_form.is_valid():
            AnswerRule.objects.create(question=question, **_get_post_values(request.POST))
            messages.success(request, 'Logic successfully added.')
            return HttpResponseRedirect('/batches/%s/questions/' % question.batch.id)
    context = {'logic_form': logic_form, 'button_label': 'Save', 'question': question}
    return render(request, "questions/logic.html", context)

@permission_required('auth.can_view_batches')
def new(request):
    response, context = _render_question_view(request)
    return response or render(request, 'questions/new.html', context)

@permission_required('auth.can_view_batches')
def edit(request, question_id):
    question = Question.objects.filter(id=question_id)
    if not question:
        messages.error(request, "Question does not exist.")
        return HttpResponseRedirect('/questions/')
    response, context = _render_question_view(request, question[0])
    return response or render(request, 'questions/new.html', context)

def delete(request, question_id):
    question = Question.objects.filter(pk=question_id)
    if question:
        messages.success(request, "Question successfully deleted.")
    else:
        messages.error(request, "Question does not exist.")
    question.delete()
    return HttpResponseRedirect("/questions/")

def _process_question_form(request, options, response, instance=None):
    question_form = QuestionForm(data=request.POST, instance=instance)
    action_str = 'edit' if instance else 'add'
    if question_form.is_valid():
        question_form.save(**request.POST)
        messages.success(request, 'Question successfully %sed.'%action_str)
        response = HttpResponseRedirect('/questions/')
    else:
        messages.error(request, 'Question was not %sed.'%action_str)
        options = dict(request.POST).get('options', None)
    return response, options, question_form

def _render_question_view(request, instance=None):
    question_form = QuestionForm(instance=instance)
    options = None
    response = None
    if instance:
        options = instance.options.all()
        options = [option.text for option in options] if options else None

    if request.method == 'POST':
        response, options, question_form = _process_question_form(request, options, response,  instance)

    context = {'button_label': 'Save',
             'id': 'add-question-form',
             'request': request,
             'questionform': question_form}

    if options:
        context['options'] = filter(lambda text: text.strip(), list(set(options)))

    return response, context

def _create_question_hash_response(questions):
    questions_to_display = map(lambda question: {'id': str(question.id), 'text':question.text}, questions)
    return HttpResponse(json.dumps(questions_to_display), mimetype='application/json')

def get_questions_for_batch(request, question_id):
    question = Question.objects.get(id=question_id)
    batch = question.batch
    return _create_question_hash_response(batch.questions.filter(subquestion=False).exclude(id=question_id))

def get_sub_questions_for_question(request, question_id):
    question = Question.objects.get(id=question_id)
    return _create_question_hash_response(question.get_subquestions())