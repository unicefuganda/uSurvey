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

    questions = HouseholdMemberGroup.objects.get(id=group_id).all_questions() if group_id \
        else Question.objects.filter(batch=batch)

    if not questions.exists():
        messages.error(request,'There are no questions associated with this batch yet.')
    context = {'questions':questions, 'request': request, 'batch':batch}
    return render(request, 'questions/index.html', context)

@permission_required('auth.can_view_batches')
def new(request, batch_id):
    question_form = QuestionForm()
    if request.method == 'POST':
        question_form = QuestionForm(data=request.POST)
        if question_form.is_valid():
            question_form.save(batch=Batch.objects.get(id=batch_id))
            messages.success(request, 'Question successfully added.')
            return HttpResponseRedirect('/batches/%s/questions/'% batch_id)
    context = { 'button_label':'Save',
                'id':'add-question-form',
                'request':request,
                'questionform':question_form}
    return render(request, 'questions/new.html', context)

def filter_by_group(request):
    group_id = request.GET['group'] if contains_key(request.GET, 'group') else None
    questions= Question.objects.filter(group__id=group_id).values('id', 'text').order_by('text')
    json_dump = json.dumps(list(questions), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')