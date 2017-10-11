import os
import json
from django.utils.safestring import mark_safe
from django.http import HttpResponse, HttpResponseRedirect,\
    HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.utils.decorators import method_decorator
from django.conf import settings
from survey.models import Survey, Location, LocationType,\
    QuestionSet, ListingTemplate, Batch,\
    Question, QuestionTemplate, QuestionOption, QuestionFlow, Answer
from survey.utils.query_helper import get_filterset
from survey.models import LocationType
from survey.models import Interview
from survey.forms.enumeration_area import LocationsFilterForm
from survey.forms.question_set import get_question_set_form
from survey.forms.question import get_question_form
from survey.forms.filters import QuestionSetResultsFilterForm
from survey.forms.filters import SurveyResultsFilterForm
from survey.odk.utils.odk_helper import get_zipped_dir
from survey.services.results_download_service import ResultsDownloadService
from django.db.models import ProtectedError

model = QuestionSet
QuestionsForm = get_question_form(Question)


class QuestionSetView(object):
    # users of this class methods needs to set their own bread crumbs
    model = QuestionSet
    questionSetForm = get_question_set_form(QuestionSet)

    def __init__(self, model_class=model, *args, **kwargs):
        if issubclass(model_class, QuestionSet):
            self.model = model_class
            self.questionSetForm = get_question_set_form(
                model_class)    # create appropriate qset form
        else:
            raise HttpResponseNotAllowed('Illegal access')

    @method_decorator(permission_required('auth.can_view_batches'))
    def index(
            self,
            request,
            qsets,
            extra_context={},
            template_name='question_set/index.html',
            **form_extra):
        search_fields = ['name', 'description']
        if 'q' in request.GET:
            qsets = get_filterset(qsets, request.GET['q'], search_fields)
        context = {
            'question_sets': qsets.order_by('-created'),
            'request': request,
            'model': self.model,
            'placeholder': 'name, description',
            'model_name' : self.model.__name__,
            'question_set_form': self.questionSetForm(
                **form_extra)}
        context.update(extra_context)

        return render(request, template_name,
                      context)

    @method_decorator(permission_required('auth.can_view_batches'))
    def new(
            self,
            request,
            extra_context={},
            template_name='question_set/new.html',
            **form_extra):
        # self._set_bread_crumbs(request)
        response = None
        if request.method == 'POST':
            qset_form = self.questionSetForm(request.POST, **form_extra)
            if qset_form.is_valid():
                qset_form = self._save_form(request, qset_form)
                messages.success(
                    request, '%s successfully added.' %
                    self.model.verbose_name())
                response = HttpResponseRedirect(
                    reverse(
                        '%s_home' %
                        self.model.resolve_tag()))
        else:
            qset_form = self.questionSetForm(**form_extra)
        # if qset_form.errors:
        #     messages.error(request, qset_form.errors.values()[0])
        cancel_url = reverse('%s_home' % self.model.resolve_tag())
        if "initial" in form_extra:
            if "survey" in form_extra['initial']:
                cancel_url = reverse('batch_index_page', args=[form_extra['initial']['survey'], ])
        context = {'question_set_form': qset_form,
                   'title': "New %s" % self.model.verbose_name(),
                   'button_label': 'Create',
                   'id': 'add-question_set-form',
                   'model': self.model,
                   'cancel_url': request.META.get('HTTP_REFERER') or cancel_url
                   }
        context.update(extra_context)
        return response or render(request, template_name, context)

    def _save_form(self, request, qset_form, **kwargs):
        return qset_form.save(**request.POST)

    @method_decorator(permission_required('auth.can_view_batches'))
    def edit(
            self,
            request,
            qset,
            extra_context={},
            template_name='question_set/new.html',
            **form_extra):
        if request.method == 'POST':
            qset_form = self.questionSetForm(instance=qset, data=request.POST)
            if qset_form.is_valid():
                qset_form = self._save_form(request, qset_form)
                messages.success(
                    request, '%s successfully edited.' %
                    self.model.verbose_name())
                return HttpResponseRedirect(
                    reverse(
                        '%s_home' %
                        self.model.resolve_tag()))
        else:
            qset_form = self.questionSetForm(instance=qset, **form_extra)
        context = {
            'request': request,
            'model': self.model,
            'listing_model': ListingTemplate,
            'id': 'edit-question-set-form',
            'placeholder': 'name, description',
            'question_set_form': qset_form,
            'action': '',
            'cancel_url': request.META.get('HTTP_REFERER') or reverse('%s_home' % self.model.resolve_tag())}
        context.update(extra_context)
        return render(request, template_name, context)

    @permission_required('auth.can_view_batches')
    def delete(self, request, qset):
        if qset.interviews.exists():
            messages.error(
                request,
                "%s cannot be deleted because it already has interviews." %
                self.model.verbose_name())
        else:
            qset.delete()
        return HttpResponseRedirect('%s_home' % self.model.resolve_tag())

@permission_required('auth.can_view_batches')
def delete(request, question_id, batch_id):
    qset = get_object_or_404(QuestionSet, pk=question_id)

    if qset.interviews.exists():
        messages.error(
            request,
            "%s cannot be deleted because it already has interviews." %
        qset.verbose_name())
    else:
        messages.success(request, "Question Set Deleted Successfully")
        qset.delete()
    return HttpResponseRedirect(
        reverse(
            'batch_index_page',
            args=(
                batch_id
            )
        ))


def delete_qset_listingform(request, question_id):
    qset = QuestionSet.get(pk=question_id)
    if qset.interviews.exists():
        messages.error(
            request,
            "%s cannot be deleted because it already has interviews." %
            qset.verbose_name())
    else:
        try:
            qset.delete()
            messages.success(request, "Listing form successfully deleted.")
        except ProtectedError as e:
            print e
            messages.success(request, "You can't delete this because it's being used by another")
            pass
    return HttpResponseRedirect(reverse('%s_home' % qset.resolve_tag()))


@login_required
@permission_required('auth.can_view_aggregates')
def view_data(request, qset_id):
    qset = QuestionSet.get(pk=qset_id)
    request.breadcrumbs(qset.edit_breadcrumbs(qset=qset))
    disabled_fields = []
    request.GET = request.GET.copy()
    request.GET['question_set'] = qset_id
    disabled_fields.append('question_set')
    if hasattr(qset, 'survey'):
        request.GET['survey'] = qset.survey.id
        disabled_fields.append('survey')
    title = 'View Data'
    return _view_qset_data(
        request,
        qset.__class__,
        Interview.objects.filter(
            question_set__id=qset_id),
        title,
        disabled_fields=disabled_fields)


@login_required
@permission_required('auth.can_view_aggregates')
def view_listing_data(request):
    interviews = Interview.objects.filter(
        question_set__id__in=ListingTemplate.objects.values_list(
            'id', flat=True))
    title = 'View Listing Data'
    return _view_qset_data(request, ListingTemplate, interviews,title)


@login_required
@permission_required('auth.can_view_aggregates')
def view_survey_data(request):
    interviews = Interview.objects.filter(
        question_set__id__in=Batch.objects.values_list(
            'id', flat=True))
    title = 'View Survey Data'
    return _view_qset_data(request, Batch, interviews,title)


def _view_qset_data(request, model_class, interviews,title, disabled_fields=[]):
    params = request.GET if request.method == 'GET' else request.POST
    survey_filter = SurveyResultsFilterForm(
        model_class, disabled_fields=disabled_fields, data=params)
    locations_filter = LocationsFilterForm(data=request.GET, include_ea=True)
    selected_qset = None
    survey = None
    items_per_page = int(params.get('max_display_per_page', 50))
    try:
        page_index = int(params.get('page', 1)) - 1
    except BaseException:
        page_index = 0
    if survey_filter.is_valid():
        interviews = survey_filter.get_interviews(interviews=interviews)
        selected_qset = survey_filter.cleaned_data['question_set']
        survey = survey_filter.cleaned_data['survey']
    if locations_filter.is_valid():
        interviews = interviews.filter(ea__in=locations_filter.get_enumerations())
    search_fields = [
        'ea__name',
        'survey__name',
        'question_set__name',
        'answer__as_text',
    ]
    if 'q' in request.GET:
        interviews = get_filterset(interviews, request.GET['q'], search_fields)
    context = {
        'survey_filter': survey_filter,
        'interviews': interviews,
        'locations_filter': locations_filter,
        'location_filter_types': LocationType.in_between(),
        'placeholder': 'Response, EA, Survey, %s' % model_class.verbose_name(),
        'selected_qset': selected_qset,
        'model_class': model_class,
        'items_per_page': items_per_page,
        'max_display_per_page': items_per_page,
        'title':title}
    if selected_qset and survey:
        # page_start = page_index * items_per_page
        # interviews = interviews[page_start: page_start + items_per_page]()
        download_service = ResultsDownloadService(
            selected_qset,
            survey=survey,
            interviews=interviews,
            page_index=page_index,
            items_per_page=items_per_page)
        df = download_service.get_interview_answers()
        context['report'] = mark_safe(
            df.to_html(
                classes='table table-striped\
                    dataTable table-bordered table-hover table-sort',
                max_rows=items_per_page))
    return render(request, 'question_set/view_all_data.html', context)

@login_required
@permission_required('auth.can_view_aggregates')
def listing_entries(request, qset_id):
    try:
        listing_qset = ListingTemplate.get(pk=qset_id)
        surveys = listing_qset.survey_settings.all()
        request.breadcrumbs(listing_qset.edit_breadcrumbs(qset=listing_qset))
        request.GET
        search_fields = ['name', ]
        if 'q' in request.GET:
            surveys = get_filterset(surveys, request.GET['q'], search_fields)
        context = {
            'question_set': listing_qset,
            'surveys': surveys,
            'placeholder': 'name,'}
        return render(request, 'question_set/listing_entries.html', context)
    except ListingTemplate.DoesNotExist:
        return HttpResponseNotFound()


@login_required
def identifiers(request):
    id = request.GET.get('id', None)
    last_question_id = request.GET.get('q_id', None)
    if last_question_id is None:
        json_dump = json.dumps(
            list(
                Question.objects.filter(
                    qset__id=id).values_list(
                    'identifier',
                    flat=True)))
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
        #         identifiers.union(qset.parameter_list.questions.values_list\
            #('identifier', flat=True))
        # except Batch.DoesNotExist:
        #     pass
        json_dump = json.dumps(list(identifiers))
    return HttpResponse(json_dump, content_type='application/json')


def clone_qset(request, qset_id):
    qset = QuestionSet.get(pk=qset_id)
    qset.deep_clone()
    messages.info(request, 'Successfully cloned %s' % qset.name)
    return HttpResponseRedirect(reverse('%s_home' % qset.resolve_tag()))


@permission_required('auth.can_view_aggregates')
def download_attachment(request, question_id, interview_id):
    question = get_object_or_404(Question, pk=question_id)
    interview = get_object_or_404(Interview, pk=interview_id)
    answer_class = Answer.get_class(question.answer_type)
    filename = '%s-%s.zip' % (question.identifier, question_id)
    attachment_dir = os.path.join(
        settings.SUBMISSION_UPLOAD_BASE,
        str(answer_class.get(
            interview=interview,
            question=question).value),
        'attachments')
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    response.write(get_zipped_dir(attachment_dir))
    return response


def download_data(request, qset_id):
    qset = QuestionSet.get(pk=qset_id)
    params = request.GET if request.method == 'GET' else request.POST
    survey_filter = QuestionSetResultsFilterForm(qset, data=params)
    locations_filter = LocationsFilterForm(data=request.GET, include_ea=True)
    interviews = survey_filter.get_interviews()
    if locations_filter.is_valid():
        interviews = interviews.filter(
            ea__in=locations_filter.get_enumerations()).order_by('created')
    last_selected_loc = locations_filter.last_location_selected
    download_service = ResultsDownloadService(qset, interviews=interviews)
    file_name = '%s%s' % ('%s-%s-' % (
        last_selected_loc.type.name,
        last_selected_loc.name) if last_selected_loc else '',
        qset.name)
    reports_df = download_service.generate_interview_reports()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;\
        filename="%s.csv"' % file_name
    reports_df.to_csv(
        response,
        date_format='%Y-%m-%d %H:%M:%S',
        encoding='utf-8')  # exclude interview id
    return response


@login_required
def list_qsets(request):
    if request.GET.get('survey_id'):
        values = Survey.get(
            id=request.GET.get('survey_id')).qsets.values(
            'id', 'name')
    else:
        values = QuestionSet.objects.values('id', 'name')
    return HttpResponse(
        json.dumps(
            list(values)),
        content_type='application/json')


@login_required
def list_questions(request):
    if request.GET.get('id'):
        values = [{
            'id': q.id,
            'identifier': q.identifier,
            'text': q.text}
            for q in QuestionSet.get(id=request.GET.get('id')).all_questions]
    else:
        values = list(
            Question.objects.all().values(
                'id', 'identifier', 'text'))
    return HttpResponse(
        json.dumps(
            list(values)),
        content_type='application/json')


@login_required
def question_validators(request):
    values = {}
    if request.GET.get('id'):
        for question in QuestionSet.get(
                id=request.GET.get('id')).all_questions:
            values['%s' % question.id] = [
                validator for validator in question.validator_names()]
    elif request.GET.get('ques_id'):
        values = Question.get(id=request.GET.get('ques_id')).validator_names()
    return HttpResponse(json.dumps(values), content_type='application/json')


@login_required
def question_options(request):
    values = {}
    if request.GET.get('id'):
        for question in QuestionSet.get(
                id=request.GET.get('id')).all_questions:
            values['%s' % question.id] = dict(
                [(opt.order, opt.text) for opt in question.options.all()])
    elif request.GET.get('ques_id'):
        values = dict(
            Question.get(
                id=request.GET.get('ques_id')).options.values_list(
                'order',
                'text'))
    return HttpResponse(json.dumps(values), content_type='application/json')
