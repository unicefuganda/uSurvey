from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import QuestionModule


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
    return render(request, 'question_module/new.html', {'question_module_form': question_module_form})


@login_required
@permission_required('auth.can_view_batches')
def index(request):
    all_question_modules = QuestionModule.objects.all()
    context = {'question_modules': all_question_modules}
    return render(request, "question_module/index.html", context)


def delete(request, module_id):
    try:
        QuestionModule.objects.get(id=module_id).delete()
        messages.success(request, "Module successfully deleted.")
    except QuestionModule.DoesNotExist:
        messages.success(request, "Module does not exist.")
    return HttpResponseRedirect("/modules/")