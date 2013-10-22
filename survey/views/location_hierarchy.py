from django.contrib import messages
from django.core import management

from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils.text import slugify
from rapidsms.contrib.locations.models import LocationType, Location
from django.forms.formsets import formset_factory

from survey.forms.location_details import LocationDetailsForm
from survey.forms.location_hierarchy import LocationHierarchyForm, BaseArticleFormSet
from survey.forms.upload_locations import UploadLocationForm
from survey.models import LocationTypeDetails
from survey.views.location_upload_view_helper import UploadLocation


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

def upload(request):
    if request.method == 'POST':
        file = request.POST.get('file', None)
        if file:
            if file.endswith('.csv'):
                uploader = UploadLocation(file)
                uploaded, message = uploader.upload()
                if uploaded:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
            else:
                messages.error(request, 'Only csv file format supported.')
        else:
            messages.error(request, 'File field cannot be empty')
        return HttpResponseRedirect('/locations/upload/')

    country_with_location_details_objects = LocationTypeDetails.objects.all()[0].country
    context = {'button_label': 'Save', 'id': 'upload-locations-form',
             'country_name': country_with_location_details_objects.name, 'upload_form': UploadLocationForm()}
    return render(request, 'location_hierarchy/upload.html', context)
