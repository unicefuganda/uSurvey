from django.shortcuts import render
from survey.models import Survey


def home(request):
    return render(request, 'home/index.html', {'surveys': Survey.objects.all()})


def about(request):
    return render(request, 'home/about.html')