import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.contrib import messages

from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import permission_required

from survey.models.batch import Batch
from survey.models.question import Question
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
    context = {'questions': questions, 'request': request, 'batch': batch}
    return render(request, 'questions/index.html', context)


@permission_required('auth.can_view_batches')
def new(request):
    response = None
    question_form = QuestionForm()
    options = None
    if request.method == 'POST':
        question_form = QuestionForm(data=request.POST)
        if question_form.is_valid():
            question_form.save(**request.POST)
            messages.success(request, 'Question successfully added.')
            response = HttpResponseRedirect('/questions/')
        else:
            messages.error(request, 'Question was not added.')
            options = dict(request.POST).get('options', None)
    context = {'button_label': 'Save',
               'id': 'add-question-form',
               'request': request,
               'questionform': question_form}
    if options:
        context['options'] = list(set(options))
    return response or render(request, 'questions/new.html', context)


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
    questions = Question.objects.all()
    context = {'questions': questions, 'request': request}
    return render(request, 'questions/index.html', context)


def __process_sub_question_form(request, questionform, parent_question):
    if questionform.is_valid():
        sub_question = questionform.save(commit=False)
        sub_question.subquestion = True
        sub_question.parent = parent_question
        sub_question.save()
        messages.success(request, 'Sub question successfully added.')
        return HttpResponseRedirect('/questions/')


def new_subquestion(request, question_id):
    parent_question = Question.objects.get(pk=question_id)
    questionform = QuestionForm()
    response = None
    if request.method == 'POST':
        questionform = QuestionForm(request.POST)
        response = __process_sub_question_form(request, questionform, parent_question)
    context = {'questionform': questionform, 'button_label': 'Save', 'id': 'add-sub_question-form'}
    return response or render(request, 'questions/new.html', context)