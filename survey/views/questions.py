from django.shortcuts import render
from survey.models import Batch, Question
from django.contrib import messages

def index(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    questions = Question.objects.filter(batch=batch)
    if not questions.exists():
        messages.error(request,'There are no questions associated with this batch yet.')
    context = {'questions':questions, 'request': request, 'batch':batch}
    return render(request, 'questions/index.html', context)
