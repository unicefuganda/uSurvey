from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.text import slugify
from survey.models import LocationType, Location
from django.forms.formsets import formset_factory

from django.http.response import HttpResponseRedirect
from survey.forms.location_details import LocationDetailsForm
from survey.forms.location_hierarchy import LocationHierarchyForm, BaseArticleFormSet
from survey.forms.upload_csv_file import UploadLocationsForm
from survey.models import LocationTypeDetails
from survey.tasks import upload_task


@login_required
@permission_required('auth.can_add_location_types')
def upload(request):
    upload_form = UploadLocationsForm()
    if request.method == 'POST':
        upload_form = UploadLocationsForm(request.POST, request.FILES)
        if upload_form.is_valid():
            #upload_form.upload()
            upload_task.delay(upload_form)
            messages.warning(request, "Upload in progress. This could take a while.")
            return HttpResponseRedirect('/locations/upload/')
        messages.error(request, 'Locations not uploaded. %s'%upload_form.errors['__all__'].as_text().replace('*',''))
    country_name = Location.objects.get(parent=None).name
    context = {'button_label': 'Save', 'id': 'upload-locations-form',
             'country_name': country_name, 'upload_form': upload_form,'range':range(3)}
    location_types = LocationType.objects.order_by('level') #get_ordered_types().exclude(name__iexact='country')
    if location_types.exists():
        context.update({'location_types':location_types})
    return render(request, 'location_hierarchy/upload.html', context)
