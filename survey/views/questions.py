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
from survey.views.views_helper import contains_key


@permission_required('auth.can_view_batches')
def index(request, batch_id):
    batch = Batch.objects.get(id=batch_id)

    group_id = request.GET.get('group_id', None)

    if group_id and group_id!='all':
        questions = HouseholdMemberGroup.objects.get(id=group_id).all_questions()
    else:
        questions = Question.objects.filter(batch=batch)

    if not questions.exists():
        messages.error(request,'There are no questions associated with this batch yet.')
    context = {'questions':questions, 'request': request, 'batch':batch}
    return render(request, 'questions/index.html', context)

@permission_required('auth.can_view_batches')
def new(request):
    question_form = QuestionForm()
    if request.method == 'POST':
        question_form = QuestionForm(data=request.POST)
        if question_form.is_valid():
            question_form.save(**request.POST)
            messages.success(request, 'Question successfully added.')
            return HttpResponseRedirect('/questions/')
    context = { 'button_label':'Save',
                'id':'add-question-form',
                'request':request,
                'questionform':question_form}
    return render(request, 'questions/new.html', context)

@permission_required('auth.can_view_batches')
def filter_by_group(request, group_id):
    if group_id.lower()!='all':
        questions= Question.objects.filter(group__id=group_id).values('id', 'text').order_by('text')
    else:
        questions = Question.objects.filter().values('id', 'text').order_by('text')
    json_dump = json.dumps(list(questions), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')

@permission_required('auth.can_view_batches')
def list_all_questions(request):
    questions = Question.objects.all()
    context = {'questions':questions, 'request': request}
    return render(request, 'questions/index.html', context)