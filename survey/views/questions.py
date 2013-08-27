from django.shortcuts import render
from survey.models import Batch, Question

def index(request, batch_id):
    batch = Batch.objects.get(id=batch_id)
    questions = Question.objects.filter(batch=batch)
    context = {'questions':questions, 'request': request, 'batch':batch}
    return render(request, 'questions/index.html', context)
