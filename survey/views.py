from django.http import HttpResponse
from django.shortcuts import render_to_response, render, redirect

def new_investigator(request):
    return render(request, 'investigators/new.html')