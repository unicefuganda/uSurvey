from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import QuestionModule, Question
from django.core.urlresolvers import reverse


@login_required
@permission_required('auth.can_view_batches')
def new(request):
    question_module_form = QuestionModuleForm()
    if request.method == 'POST':
        question_module_form = QuestionModuleForm(request.POST)
        if question_module_form.is_valid():
            question_module_form.save()
            messages.success(request, "Question module successfully created.")
            return HttpResponseRedirect("/modules/")
        messages.error(request, "Question module was not created.")
    request.breadcrumbs([
        ('Modules', reverse('question_module_listing_page')),
    ])
    return render(request, 'question_module/new.html',
                  {'question_module_form': question_module_form, 'title': 'New Module', 'button_label': 'Create',
                   'action': '/modules/new/'})


@permission_required('auth.can_view_batches')
def index(request):
    all_question_modules = QuestionModule.objects.all()
    context = {'question_modules': all_question_modules}
    return render(request, "question_module/index.html", context)

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
    request.breadcrumbs([
        ('Modules', reverse('question_module_listing_page')),
    ])
    return response or render(request, 'question_module/new.html',
                  {'question_module_form': question_module_form, 'title': 'Edit Module', 'button_label': 'Save',
                   'action': '/modules/%s/edit/' % module.id})