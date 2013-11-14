from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required

from django.http.response import HttpResponseRedirect
from django.shortcuts import render

from survey.forms.upload_locations import UploadWeightsForm


@login_required
@permission_required('auth.can_view_batches')
def upload(request):
    upload_form = UploadWeightsForm()
    if request.method == 'POST':
        upload_form = UploadWeightsForm(request.POST, request.FILES)
        if upload_form.is_valid():
            status, message = upload_form.upload()
            message_status = messages.SUCCESS if status else messages.ERROR
            messages.add_message(request, message_status, message)
            return HttpResponseRedirect('/locations/weights/upload/')

    context = {'button_label': 'Upload', 'id': 'upload-location-weights-form',
               'upload_form': upload_form,'range':range(3)}

    return render(request, 'locations/weights/upload.html', context)
