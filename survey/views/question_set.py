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


def delete(request, question_id,batch_id):
    qset = QuestionSet.get(pk=question_id)
    print batch_id,"contextname"
    if qset.interviews.exists():
        messages.error(request,
                       "%s cannot be deleted because it already has interviews." % qset.verbose_name())
    else:
        qset.delete()
    return HttpResponseRedirect('/surveys/%s/batches/'%batch_id)

def delete_qset_listingform(request, question_id):
    qset = QuestionSet.get(pk=question_id)
    if qset.interviews.exists():
        messages.error(request,
                       "%s cannot be deleted because it already has interviews." % qset.verbose_name())
    else:
        qset.delete()
    return HttpResponseRedirect('/listing_form/')
