from django.shortcuts import render
from survey.models import Batch, Question

def index(request, batch_id):
    return render(request, 'questions/index.html')
