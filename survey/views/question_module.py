from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import QuestionModule


def new(request):
    question_module_form = QuestionModuleForm()
    if request.method == 'POST':
        question_module_form = QuestionModuleForm(request.POST)
        if question_module_form.is_valid():
            question_module_form.save()
            messages.success(request, "Question module successfully created.")
            return HttpResponseRedirect("/modules/")
        messages.error(request, "Question module was not created.")
    return render_to_response('question_module/new.html', {'question_module_form': question_module_form})


def index(request):
    all_question_modules = QuestionModule.objects.all()
    context = {'question_modules': all_question_modules}
    return render_to_response("question_module/index.html", context)