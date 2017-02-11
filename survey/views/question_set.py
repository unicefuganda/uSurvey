import ast
import os
import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.utils.decorators import method_decorator
from django.forms import ValidationError
from django.conf import settings
from survey.services.export_interviewers import ExportInterviewersService
from survey.models import Survey, Location, LocationType, QuestionSet, ListingTemplate, Batch, \
    Question, QuestionTemplate, QuestionOption, QuestionFlow, Answer
from survey.forms.surveys import SurveyForm
from survey.views.custom_decorators import handle_object_does_not_exist
from survey.utils.query_helper import get_filterset
from survey.models import EnumerationArea, LocationType, Location, BatchCommencement, SurveyHouseholdListing
from survey.models import Interview
from survey.forms.enumeration_area import EnumerationAreaForm, LocationsFilterForm
from survey.forms.question_set import get_question_set_form
from survey.forms.question import get_question_form
from survey.forms.filters import QuestionFilterForm
from survey.odk.utils.odk_helper import get_zipped_dir
from survey.services.results_download_service import ResultsDownloadService, ResultComposer

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
                   'action': '', 'cancel_url': reverse('%s_home'%self.model.resolve_tag())}
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


def delete(request, question_id, batch_id):
    qset = QuestionSet.get(pk=question_id)
    if qset.interviews.exists():
        messages.error(request,
                       "%s cannot be deleted because it already has interviews." % qset.verbose_name())
    else:
        qset.delete()
    return HttpResponseRedirect(reverse('batch_index_page', args=(qset.survey.id,)))


def delete_qset_listingform(request, question_id):
    qset = QuestionSet.get(pk=question_id)
    if qset.interviews.exists():
        messages.error(request,
                       "%s cannot be deleted because it already has interviews." % qset.verbose_name())
    else:
        qset.delete()
    return HttpResponseRedirect(reverse('%s_home' % qset.resolve_tag()))


@login_required
@permission_required('auth.can_view_aggregates')
def view_data(request, qset_id, survey_id):
    try:
        qset = QuestionSet.get(pk=qset_id)
        survey = Survey.get(id=survey_id)
        request.breadcrumbs(qset.edit_breadcrumbs(qset=qset))
        params = request.GET
        locations_filter = LocationsFilterForm(data=request.GET, include_ea=True)
        if locations_filter.is_valid():
            interviews = Interview.objects.filter(ea__in=locations_filter.get_enumerations(),
                                                  question_set=qset).order_by('created')
        context = {'qset': qset, 'survey': survey, 'interviews': interviews, 'locations_filter': locations_filter,
                   'location_filter_types': LocationType.in_between()}
        return render(request, 'question_set/view_data.html', context)
    except QuestionSet.DoesNotExist:
        return HttpResponseNotFound()



@login_required
@permission_required('auth.can_view_aggregates')
def listing_entries(request, qset_id):
    try:
        listing_qset = ListingTemplate.get(pk=qset_id)
        surveys = listing_qset.survey_settings.all()
        request.breadcrumbs(listing_qset.edit_breadcrumbs(qset=listing_qset))
        params = request.GET
        search_fields = ['name', ]
        if request.GET.has_key('q'):
            surveys = get_filterset(surveys, request.GET['q'], search_fields)
        context = {'question_set': listing_qset, 'surveys': surveys, }
        return render(request, 'question_set/listing_entries.html', context)
    except ListingTemplate.DoesNotExist:
        return HttpResponseNotFound()

@login_required
def identifiers(request):
    id = request.GET.get('id', None)
    last_question_id = request.GET.get('q_id', None)
    if last_question_id is None:
        json_dump = json.dumps(list(Question.objects.filter(qset__id=id).values_list('identifier', flat=True)))
    else:
        # return questions before last question
        qset = QuestionSet.get(pk=id)
        identifiers = set()
        for question in qset.flow_questions:
            if int(question.id) == int(last_question_id):
                break
            identifiers.add(question.identifier)
        # try:
        #     qset = Batch.get(pk=qset.pk)
        #     if hasattr(qset, 'parameter_list'):
        #         identifiers.union(qset.parameter_list.questions.values_list('identifier', flat=True))
        # except Batch.DoesNotExist:
        #     pass
        json_dump = json.dumps(list(identifiers))
    return HttpResponse(json_dump, content_type='application/json')


def clone_qset(request, qset_id):
    qset = QuestionSet.get(pk=qset_id)
    qset.deep_clone()
    messages.info(request, 'Successfully cloned %s' % qset.name)
    return HttpResponseRedirect(reverse('%s_home'% qset.resolve_tag()))


@permission_required('auth.can_view_aggregates')
def download_attachment(request, question_id, interview_id):
    question = get_object_or_404(Question, pk=question_id)
    interview = get_object_or_404(Interview, pk=interview_id)
    answer_class = Answer.get_class(question.answer_type)
    filename = '%s-%s.zip' % (question.identifier, question_id)
    attachment_dir = os.path.join(
        settings.SUBMISSION_UPLOAD_BASE, str(answer_class.get(interview=interview, question=question).value),
        'attachments')
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    response.write(get_zipped_dir(attachment_dir))
    return response


def download_data(request, qset_id, survey_id):
    qset = QuestionSet.get(pk=qset_id)
    survey = Survey.get(pk=survey_id)
    locations_filter = LocationsFilterForm(data=request.GET)
    last_selected_loc = locations_filter.last_location_selected
    restricted_to = None
    if last_selected_loc:
        restricted_to = [last_selected_loc, ]
    download_service = ResultsDownloadService(batch=qset, survey=survey, restrict_to=restricted_to)
    file_name = '%s%s' % ('%s-%s-' % (last_selected_loc.type.name, last_selected_loc.name) if
                          last_selected_loc else '', qset.name)
    reports_df = download_service.generate_interview_reports()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % file_name
    reports_df.to_csv(response, date_format='%Y-%m-%d %H:%M:%S')   #exclude interview id
    return response
