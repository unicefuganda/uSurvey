from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from survey.models import EnumerationArea
from django.utils.timezone import utc
from survey.forms.upload_csv_file import UploadEAForm
from survey.forms.enumeration_area import EnumerationAreaForm
from survey.services.ea_upload import UploadEACSVLayoutHelper
from survey.tasks import upload_task



@login_required
@permission_required('auth.can_view_batches')
def new(request):
    enumeration_area_form = EnumerationAreaForm()
    if request.method == 'POST':
        enumeration_area_form = EnumerationAreaForm(request.POST)
        if enumeration_area_form.is_valid():
            enumeration_area_form.save()
            messages.success(request, "Enumeration Area successfully created.")
            return HttpResponseRedirect(reverse('enumeration_area_home', args=()))
        messages.error(request, "Enumeration area was not created.")
    return render(request, 'enumeration_area/new.html',
                  {'enumeration_area_form': enumeration_area_form, 'title': 'New Enumeration Area', 'button_label': 'Create',
                   'action': reverse('enumeration_area_home', args=())})


@permission_required('auth.can_view_batches')
def index(request):
    enumeration_areas = EnumerationArea.objects.all()
    context = {'enumeration_areas': enumeration_areas}
    return render(request, "enumeration_area/index.html", context)

@permission_required('auth.can_view_batches')
def delete(request, module_id):
    try:
        module = QuestionModule.objects.get(id=module_id)
        module.remove_related_questions()
        module.delete()
        messages.success(request, "Module successfully deleted.")
    except QuestionModule.DoesNotExist:
        messages.success(request, "Module does not exist.")
    return HttpResponseRedirect("/modules/")


def _process_form(request, question_module_form):
    if question_module_form.is_valid():
        question_module_form.save()
        messages.success(request, "Question module successfully edited.")
    return question_module_form, HttpResponseRedirect("/modules/")

@permission_required('auth.can_view_batches')
def edit(request, module_id):
    response = None
    module = QuestionModule.objects.get(id=module_id)
    question_module_form = QuestionModuleForm(instance=module)
    if request.method == 'POST':
        question_module_form = QuestionModuleForm(instance=module, data=request.POST)
        question_module_form, response = _process_form(request, question_module_form)
    return response or render(request, 'question_module/new.html',
                  {'question_module_form': question_module_form, 'title': 'Edit Module', 'button_label': 'Save',
                   'action': '/modules/%s/edit/' % module.id})




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