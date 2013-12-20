from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render

from django.utils.timezone import utc
from survey.forms.upload_csv_file import UploadEAForm
from survey.services.ea_upload import UploadEACSVLayoutHelper
from survey.tasks import upload_task


@permission_required('auth.can_view_batches')
def upload(request):
    upload_form = UploadEAForm()

    if request.method == 'POST':
        upload_form = UploadEAForm(request.POST, request.FILES)
        if upload_form.is_valid():
            upload_task.delay(upload_form)
            messages.warning(request, "Upload in progress. This could take a while.")
            return HttpResponseRedirect('/locations/enumeration_area/upload/')

    context = {'button_label': 'Upload', 'id': 'upload-location-ea-form', 'upload_form': upload_form,
               'csv_layout': UploadEACSVLayoutHelper()}

    return render(request, 'locations/enumeration_area/upload.html', context)