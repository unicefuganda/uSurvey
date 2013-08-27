from django.shortcuts import render
from survey.models import Batch, Question

def index(request, batch_id):
    questions = Question.objects.filter(batch__id=batch_id)
    return render(request, 'questions/index.html', {'questions':questions, 'request': request})
