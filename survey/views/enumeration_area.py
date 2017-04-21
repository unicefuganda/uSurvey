from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from survey.models import EnumerationArea, LocationType, Location
from survey.forms.enumeration_area import EnumerationAreaForm,\
    LocationsFilterForm
from survey.services.ea_upload import UploadEACSVLayoutHelper
from django_rq import job
import json
from survey.utils.query_helper import get_filterset


@job('upload_task')
def uploadtask(composer):
    composer.uploadtask()


@login_required
@permission_required('auth.can_view_batches')
def new(request):
    locations_filter = LocationsFilterForm(data=request.GET)
    enumeration_area_form = EnumerationAreaForm(
        locations=locations_filter.get_locations())
    if request.method == 'POST':
        enumeration_area_form = EnumerationAreaForm(data=request.POST)
        if enumeration_area_form.is_valid():
            enumeration_area_form.save()
            messages.success(request, "Enumeration Area successfully created.")
            return HttpResponseRedirect(
                reverse('enumeration_area_home', args=()))
        messages.error(request, "Enumeration area was not created.")
    request.breadcrumbs([
        ('Enumeration Areas', reverse('enumeration_area_home')),
    ])
    return render(request,
                  'enumeration_area/new.html',
                  {'enumeration_area_form': enumeration_area_form,
                   'locations_filter': locations_filter,
                   'title': 'New Enumeration Area',
                   'button_label': 'Create',
                   'action': reverse('new_enumeration_area_page',
                                     args=()),
                   'location_filter_types': LocationType.in_between(),
                   'redirect_url': '/enumeration_area'})


@permission_required('auth.can_view_batches')
def index(request):
    locations_filter = LocationsFilterForm(data=request.GET)
    enumeration_areas = locations_filter.get_enumerations()
    search_fields = ['name', 'locations__name', ]
    if 'q' in request.GET:
        enumeration_areas = get_filterset(
            enumeration_areas, request.GET['q'], search_fields)
    loc_types = LocationType.in_between()
    context = {'enumeration_areas': enumeration_areas,
               'locations_filter': locations_filter,
               'location_filter_types': loc_types,
               'placeholder': 'name, location name'}
    return render(request, "enumeration_area/index.html", context)


@permission_required('auth.can_view_batches')
def location_filter(request):
    locations_filter = LocationsFilterForm(data=request.GET)
    locations = locations_filter.get_locations().values(
        'id', 'name', ).order_by('name')
    json_dump = json.dumps(list(locations), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')


@permission_required('auth.can_view_batches')
def open_surveys(request):
    ea_id = request.GET['ea_id']
    ea = get_object_or_404(EnumerationArea, pk=ea_id)
    open_surveys = [dict([('id', s.pk), ('name', s.name)])
                    for s in ea.open_surveys()]
    json_dump = json.dumps(open_surveys, cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')


@permission_required('auth.can_view_batches')
def enumeration_area_filter(request):
    locations_filter = LocationsFilterForm(data=request.GET)
    enumeration_areas = locations_filter.get_enumerations()
    eas = enumeration_areas.values('id', 'name', ).order_by('name')
    json_dump = json.dumps(list(eas), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')


@permission_required('auth.can_view_batches')
def location_sub_types(request):
    kwargs = {'type__parent__pk': request.GET.get('type')}
    if request.GET.get('parent_loc', None):
        kwargs['parent__pk'] = request.GET['parent_loc']
    child_locations = Location.objects.filter(**kwargs)
    locations = child_locations.values('id', 'name', ).order_by('name')
    parent_loc = child_locations[0].parent
    eas = EnumerationArea.objects.filter(
        locations__in=parent_loc.get_leafnodes(True)).values(
        'id', 'name')
    json_dump = json.dumps(
        {'sub_type': child_locations[0].type.name,
            'locations': list(locations),
            'eas': list(eas)}, cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')


@permission_required('auth.can_view_batches')
def delete(request, ea_id):
    ea = get_object_or_404(EnumerationArea, pk=ea_id)
    ea.delete()
    return HttpResponseRedirect(reverse('enumeration_area_home', args=()))


@permission_required('auth.can_view_batches')
def edit(request, ea_id):
    ea = get_object_or_404(EnumerationArea, pk=ea_id)
    if request.GET:
        data = request.GET
    else:
        data = dict([(loc.type.name, loc.pk) for loc in ea.parent_locations()])
    locations_filter = LocationsFilterForm(data=data)
    enumeration_area_form = EnumerationAreaForm(
        instance=ea, locations=locations_filter.get_locations())
    if request.method == 'POST':
        enumeration_area_form = EnumerationAreaForm(
            data=request.POST,
            instance=ea,
            locations=locations_filter.get_locations())

        if enumeration_area_form.is_valid():
            enumeration_area_form.save()
            messages.success(request, "Enumeration Area successfully Changed.")
            return HttpResponseRedirect(
                reverse('enumeration_area_home', args=()))
        messages.error(request, "Enumeration area was not Changed.")
    request.breadcrumbs([
        ('Enumeration Areas',
            reverse('enumeration_area_home')),
    ])
    return render(request,
                  'enumeration_area/new.html',
                  {'enumeration_area_form': enumeration_area_form,
                   'locations_filter': locations_filter,
                   'title': 'New Enumeration Area',
                   'button_label': 'Create',
                   'action': reverse('edit_enumeration_area_page',
                                     args=(ea_id,
                                           )),
                   'location_filter_types': LocationType.in_between(),
                   })


def _process_form(request, form, instance=None):
    pass
