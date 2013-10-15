from django.shortcuts import render
from survey.forms.location_hierarchy import LocationHierarchyForm


def add(request):
    return render(request,'location_hierarchy/new.html',{'hierarchy_form': LocationHierarchyForm(),'button_label':'Create Hierarchy'})