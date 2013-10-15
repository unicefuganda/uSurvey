from django.shortcuts import render
from survey.forms.location_hierarchy import LocationHierarchyForm


def add(request):
    context = {'hierarchy_form': LocationHierarchyForm(), 'button_label': 'Create Hierarchy','id':'hierarchy-form'}
    return render(request,'location_hierarchy/new.html', context)