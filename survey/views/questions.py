from django.shortcuts import render
from survey.models import Batch, Question
from django.contrib import messages
from survey.forms.question import QuestionForm
from django.http import HttpResponseRedirect

def index(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    questions = Question.objects.filter(batch=batch)
    if not questions.exists():
        messages.error(request,'There are no questions associated with this batch yet.')
    context = {'questions':questions, 'request': request, 'batch':batch}
    return render(request, 'questions/index.html', context)

def new(request, batch_id):
    question_form = QuestionForm()
    if request.method == 'POST':
        question_form = QuestionForm(data=request.POST)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.batch=Batch.objects.get(id=batch_id)
            question.save()
            messages.success(request, 'Question successfully added.')
            return HttpResponseRedirect('/batches/%s/questions/'% batch_id)
    context = { 'button_label':'Save',
                'id':'add-question-form',
                'request':request,
                'questionform':question_form}
    return render(request, 'questions/new.html', context)