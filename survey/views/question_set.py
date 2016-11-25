import ast
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.forms import ValidationError
from survey.models import Survey, Location, LocationType, QuestionSet, ListingTemplate, Batch, \
    Question, QuestionTemplate, QuestionOption, QuestionFlow
from survey.forms.surveys import SurveyForm
from survey.views.custom_decorators import handle_object_does_not_exist
from survey.utils.query_helper import get_filterset
from survey.models import EnumerationArea, LocationType, Location, BatchCommencement, SurveyHouseholdListing
from survey.forms.enumeration_area import EnumerationAreaForm, LocationsFilterForm
from survey.forms.question_set import get_question_set_form
from survey.forms.question import get_question_form
from survey.forms.filters import QuestionFilterForm
from django.conf import settings

model = QuestionSet
QuestionsForm = get_question_form(Question)


class QuestionSetView(object):
    # users of this class methods needs to set their own bread crumbs
    model = QuestionSet
    questionSetForm = get_question_set_form(QuestionSet)

    def __init__(self, model_class=model, *args, **kwargs):
        if issubclass(model_class, QuestionSet):
            self.model = model_class
            self.questionSetForm = get_question_set_form(model_class)    # create appropriate qset form
        else:
            raise HttpResponseNotAllowed('Illegal access')

    @method_decorator(permission_required('auth.can_view_batches'))
    def index(self, request, qsets, extra_context={}, template_name='question_set/index.html', **form_extra):
        search_fields = ['name', 'description']
        if request.GET.has_key('q'):
            qsets = get_filterset(qsets, request.GET['q'], search_fields)
        context = {'question_sets': qsets, 'request': request, 'model': self.model,
                   'placeholder': 'name, description', 'question_set_form': self.questionSetForm(**form_extra)}
        context.update(extra_context)
        return render(request, template_name,
                      context)

    @method_decorator(permission_required('auth.can_view_batches'))
    def new(self, request, extra_context={}, template_name='question_set/new.html', **form_extra):
        # self._set_bread_crumbs(request)
        response = None
        if request.method == 'POST':
            qset_form = self.questionSetForm(request.POST, **form_extra)
            if qset_form.is_valid():
                qset_form = self._save_form(request, qset_form)
                messages.success(request, '%s successfully added.' % self.model.verbose_name())
                response = HttpResponseRedirect(reverse('%s_home' % self.model.resolve_tag()))
        else:
            qset_form = self.questionSetForm(**form_extra)
        # if qset_form.errors:
        #     messages.error(request, qset_form.errors.values()[0])
        context = {'question_set_form': qset_form,
                   'title': "New %s" % self.model.verbose_name(),
                   'button_label': 'Create',
                   'id': 'add-question_set-form',
                   'model': self.model,
                   'cancel_url': reverse('%s_home'%self.model.resolve_tag()),
                   }
        context.update(extra_context)
        return response or render(request, template_name, context)

    def _save_form(self, request, qset_form, **kwargs):
        return qset_form.save(**request.POST)

    @method_decorator(permission_required('auth.can_view_batches'))
    def edit(self, request, qset, extra_context={}, template_name='question_set/new.html', **form_extra):
        if request.method == 'POST':
            qset_form = self.questionSetForm(instance=qset, data=request.POST)
            if qset_form.is_valid():
                qset_form = self._save_form(request, qset_form)
                messages.success(request, '%s successfully edited.' % self.model.verbose_name())
                return HttpResponseRedirect(reverse('%s_home'%self.model.resolve_tag()))
        else:
            qset_form = self.questionSetForm(instance=qset, **form_extra)
        context = {'request': request, 'model': self.model, 'listing_model': ListingTemplate,
                   'id': 'edit-question-set-form', 'placeholder': 'name, description', 'question_set_form': qset_form,
                   'action': ''}
        context.update(extra_context)
        return render(request, template_name, context)

    @permission_required('auth.can_view_batches')
    def delete(self, request, qset):
        if qset.interviews.exists():
            messages.error(request,
                           "%s cannot be deleted because it already has interviews." % self.model.verbose_name())
        else:
            qset.delete()
        return HttpResponseRedirect('%s_home'%self.model.resolve_tag())

    @method_decorator(permission_required('auth.can_view_batches'))
    def assign(self, request, qset_id):
        qset = self.model.objects.get(id=qset_id)
        batch_questions_form = QuestionsForm(qset)
        if request.method == 'POST':
            data = dict(request.POST)
            last_question = qset.last_question_inline()
            lib_questions = QuestionTemplate.objects.filter(
                identifier__in=data.get('identifier', ''))
            # print 'data: ', data, 'lib questions: ', lib_questions
            if lib_questions:
                for lib_question in lib_questions:
                    question = Question.objects.create(identifier=lib_question.identifier,
                                                       text=lib_question.text,
                                                       answer_type=lib_question.answer_type,
                                                       qset=qset,
                                                       )
                    # assign the options
                    for option in lib_question.options.all():
                        QuestionOption.objects.create(
                            question=question, text=option.text, order=option.order)
                    if last_question:
                        QuestionFlow.objects.create(
                            question=last_question, next_question=question)
                    else:
                        qset.start_question = question
                        qset.save()
                    last_question = question
    #         batch_questions_form = BatchQuestionsForm(batch=batch, data=request.POST, instance=batch)
            success_message = "Questions successfully assigned to batch: %s." % qset.name.capitalize()
            messages.success(request, success_message)
            return HttpResponseRedirect(reverse("batch_questions_page",  args=(qset.id, )))
        used_identifiers = [
            question.identifier for question in qset.questions.all()]
        library_questions = QuestionTemplate.objects.exclude(
            identifier__in=used_identifiers).order_by('identifier')
        question_filter_form = QuestionFilterForm()
    #     library_questions =  question_filter_form.filter(library_questions)
        request.breadcrumbs([
            reverse('%s_home'%self.model.resolve_tag())
        ])
        context = {'batch_questions_form': unicode(batch_questions_form), 'batch': qset,
                   'button_label': 'Save', 'id': 'assign-question-to-batch-form',
                   'library_questions': library_questions, 'question_filter_form': question_filter_form,}
        return render(request, 'batches/assign.html',
                      context)


    @permission_required('auth.can_view_batches')
    def update_orders(request, qset_id):
        qset = QuestionSet.objects.get(id=qset_id)
        new_orders = request.POST.getlist('order_information', None)
        if len(new_orders) > 0:
            # wipe off present inline flows
            inlines = qset.questions_inline()
            start_question = inlines.pop(0)
            question = start_question
            for next_question in inlines:
                QuestionFlow.objects.filter(
                    question=question, next_question=next_question).delete()
                question = next_question
            order_details = []
            map(lambda order: order_details.append(order.split('-')), new_orders)
            order_details = sorted(
                order_details, key=lambda detail: int(detail[0]))
            # recreate the flows
            questions = qset.questions.all()
            if questions:  # so all questions can be fetched once and cached
                question_id = order_details.pop(0)[1]
                start_question = questions.get(pk=question_id)
                for order, next_question_id in order_details:
                    QuestionFlow.objects.create(question=questions.get(pk=question_id),
                                                next_question=questions.get(pk=next_question_id))
                    question_id = next_question_id
                qset.start_question = start_question
                qset.save()

            success_message = "Question orders successfully updated for batch: %s." % qset.name.capitalize()
            messages.success(request, success_message)
        else:
            messages.error(request, 'No questions orders were updated.')
        return HttpResponseRedirect("/batches/%s/questions/" % qset.id)
