from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils.text import slugify
from rapidsms.contrib.locations.models import LocationType
from survey.forms.location_hierarchy import LocationHierarchyForm


def add(request):
    if request.method == 'POST':
        levels = dict(request.POST).get('levels')
        for level in levels:
            LocationType.objects.get_or_create(name=level, slug=slugify(level))
        return HttpResponseRedirect('/')
    context = {'hierarchy_form': LocationHierarchyForm(), 'button_label': 'Create Hierarchy', 'id': 'hierarchy-form'}
    return render(request,'location_hierarchy/new.html', context)