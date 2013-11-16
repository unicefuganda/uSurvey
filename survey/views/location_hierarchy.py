from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.text import slugify
from rapidsms.contrib.locations.models import LocationType, Location
from django.forms.formsets import formset_factory

from django.http.response import HttpResponseRedirect
from survey.forms.location_details import LocationDetailsForm
from survey.forms.location_hierarchy import LocationHierarchyForm, BaseArticleFormSet
from survey.forms.upload_csv_file import UploadLocationsForm
from survey.models import LocationTypeDetails
from survey.tasks import upload_task

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
                    details.location_type = location_type
                    details.country = selected_country
                    details.save()
                messages.success(request, "Location Hierarchy successfully created.")
                return HttpResponseRedirect('/')
        else:
            messages.error(request,"levels not saved")

    else:

        hierarchy_form = LocationHierarchyForm()
        details_formset = DetailsFormSet()

    context = {'hierarchy_form': hierarchy_form, 'button_label': 'Create Hierarchy', 'id': 'hierarchy-form',
               'details_formset':details_formset, 'cancel_url':'/'}
    return render(request,'location_hierarchy/new.html', context)

@login_required
@permission_required('auth.can_add_location_types')
def upload(request):
    upload_form = UploadLocationsForm()
    if request.method == 'POST':
        upload_form = UploadLocationsForm(request.POST, request.FILES)
        if upload_form.is_valid():
            upload_task.delay(upload_form)
            messages.warning(request, "Upload in progress. This could take a while.")
            return HttpResponseRedirect('/locations/upload/')
        messages.error(request, 'Locations not uploaded. %s'%upload_form.errors['__all__'].as_text().replace('*',''))

    context = {'button_label': 'Save', 'id': 'upload-locations-form',
             'country_name': '', 'upload_form': upload_form,'range':range(3)}

    details = LocationTypeDetails.objects.all()
    if not details.exists():
        messages.error(request, "No location hierarchy added yet.")
        return render(request, 'location_hierarchy/upload.html', context)

    country_with_location_details_objects = details[0].country
    context = {'button_label': 'Save', 'id': 'upload-locations-form',
             'country_name': country_with_location_details_objects.name, 'upload_form': upload_form,'range':range(3)}
    location_types = LocationTypeDetails.objects.order_by('order') #get_ordered_types().exclude(name__iexact='country')
    if location_types.exists():
        context.update({'location_types_details':location_types})
    return render(request, 'location_hierarchy/upload.html', context)
