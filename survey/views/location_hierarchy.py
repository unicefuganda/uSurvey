from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

from django.contrib.auth.decorators import permission_required, login_required
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils.text import slugify
from rapidsms.contrib.locations.models import LocationType, Location
from django.forms.formsets import formset_factory

from survey.forms.location_details import LocationDetailsForm
from survey.forms.location_hierarchy import LocationHierarchyForm, BaseArticleFormSet
from survey.forms.upload_locations import UploadLocationForm
from survey.models import LocationTypeDetails


@login_required
@permission_required('auth.can_add_location_types')
def add(request):
    DetailsFormSet = formset_factory(LocationDetailsForm, formset=BaseArticleFormSet)
    if request.method == 'POST':
        hierarchy_form = LocationHierarchyForm(request.POST)
        details_formset = DetailsFormSet(request.POST,prefix='form')

        if hierarchy_form.is_valid():
            selected_country = Location.objects.get(id=request.POST['country'])

            if details_formset.is_valid():
                for form in details_formset.forms:
                    location_type, status = LocationType.objects.get_or_create(name=form.cleaned_data.get('levels'), slug =slugify(form.cleaned_data.get('levels')))
                    details = form.save(commit=False)
                    details.location_type=location_type
                    details.country = selected_country
                    details.save()
                messages.success(request, "Location Hierarchy successfully created.")
                return HttpResponseRedirect('/')
        else:
            messages.error(request,"levels not saved")

    else:

        hierarchy_form = LocationHierarchyForm()
        details_formset = DetailsFormSet()

    context = {'hierarchy_form': hierarchy_form, 'button_label': 'Create Hierarchy', 'id': 'hierarchy-form','details_formset':details_formset}
    return render(request,'location_hierarchy/new.html', context)

@login_required
@permission_required('auth.can_add_location_types')
def upload(request):
    upload_form = UploadLocationForm()
    if request.method == 'POST':
        upload_form = UploadLocationForm(request.POST, request.FILES)
        upload_form.is_valid()
        if upload_form.is_valid():
            status, message = upload_form.upload()
            messages.success(request, message)
            return HttpResponseRedirect('/locations/upload/')

    details = LocationTypeDetails.objects.all()
    if not details.exists():
        messages.error(request, "No location hierarchy added yet.")
        return HttpResponseRedirect('/locations/upload/')

    country_with_location_details_objects = details[0].country
    context = {'button_label': 'Save', 'id': 'upload-locations-form',
             'country_name': country_with_location_details_objects.name, 'upload_form': upload_form,'range':range(3)}
    location_types = LocationType.objects.exclude(name__iexact='country')
    if location_types.exists():
        context.update({'location_types':location_types})
    return render(request, 'location_hierarchy/upload.html', context)
