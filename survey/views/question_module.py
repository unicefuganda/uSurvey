from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import QuestionModule, Question


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
    return render(request, 'question_module/new.html',
                  {'question_module_form': question_module_form, 'heading': 'Edit Module', 'button-label': 'Save',
                   'action': '/modules/new/'})


@login_required
@permission_required('auth.can_view_batches')
def index(request):
    all_question_modules = QuestionModule.objects.all()
    context = {'question_modules': all_question_modules}
    return render(request, "question_module/index.html", context)


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


def edit(request, module_id):
    response = None
    module = QuestionModule.objects.get(id=module_id)
    question_module_form = QuestionModuleForm(instance=module)
    if request.method == 'POST':
        question_module_form = QuestionModuleForm(instance=module, data=request.POST)
        question_module_form, response = _process_form(request, question_module_form)
    return response or render(request, 'question_module/new.html',
                  {'question_module_form': question_module_form, 'heading': 'Edit Module', 'button-label': 'Save',
                   'action': '/modules/%s/edit/' % module.id})