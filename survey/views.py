from django.http import HttpResponse
from django.shortcuts import render_to_response, render, redirect
from investigator_configs import *

def new_investigator(request):
    return render(request, 'investigators/new.html', {'list_of_eductional_levels': LEVEL_OF_EDUCATION, 'list_of_languages': LANGUAGES })