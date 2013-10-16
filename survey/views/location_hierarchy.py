from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils.text import slugify
from rapidsms.contrib.locations.models import LocationType
from survey.forms.location_hierarchy import LocationHierarchyForm


def add(request):
    hierarchy_form = LocationHierarchyForm()
    if request.method == 'POST':
        hierarchy_form = LocationHierarchyForm(data=request.POST)
        if hierarchy_form.is_valid():
            levels = dict(request.POST).get('levels')
            for level in levels:
                LocationType.objects.get_or_create(name=level, slug=slugify(level))
            return HttpResponseRedirect('/')
        messages.error(request, 'Levels not saved')
    context = {'hierarchy_form': hierarchy_form, 'button_label': 'Create Hierarchy', 'id': 'hierarchy-form'}
    return render(request,'location_hierarchy/new.html', context)