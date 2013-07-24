import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages

from survey.investigator_configs import *

def home(request):
    return render(request, 'home/about.html')
