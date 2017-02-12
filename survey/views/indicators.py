import json
from django import template
from django.utils.datastructures import SortedDict
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from survey.models import LocationType, Location, MultiChoiceAnswer, Interview
from survey.forms.indicator import IndicatorForm, IndicatorVariableForm
from survey.forms.filters import IndicatorFilterForm, IndicatorMetricFilterForm
from survey.models import Indicator, Survey, Answer, IndicatorVariable, IndicatorVariableCriteria
from survey.forms.enumeration_area import LocationsFilterForm


@permission_required('auth.can_view_batches')
def new(request):
    indicator_form = IndicatorForm()
    if request.method == 'POST':
        indicator_form = IndicatorForm(request.POST)
        if indicator_form.is_valid():
            indicator_form.save()
            messages.success(request, "Indicator successfully created.")
            return HttpResponseRedirect(reverse('list_indicator_page'))
        messages.error(request, "Indicator was not created.")
    request.breadcrumbs([
        ('Indicators', reverse('list_indicator_page')),
    ])
    return render(request, 'indicator/new.html',
                  {'indicator_form': indicator_form, 'title': 'Add Indicator', 'button_label': 'Create',
                   'cancel_url': reverse('list_indicator_page'), 'action': '/indicators/new/'})


def _process_form(indicator_filter_form, indicators):
    if indicator_filter_form.is_valid():
        survey_id = indicator_filter_form.cleaned_data['survey']
        batch_id = indicator_filter_form.cleaned_data['batch']
        module_id = indicator_filter_form.cleaned_data['module']
        if batch_id.isdigit() and module_id.isdigit():
            indicators = indicators.filter(batch=batch_id, module=module_id)
        elif not batch_id.isdigit() and module_id.isdigit():
            indicators = indicators.filter(module=module_id)
        elif batch_id.isdigit() and not module_id.isdigit():
            indicators = indicators.filter(parameter__qset__id=batch_id)
        elif survey_id.isdigit():
            batches = Survey.objects.get(id=survey_id).batches.values_list('id', flat=True)
            indicators = indicators.filter(parameter__qset__id__in=batches)
    return indicators


@permission_required('auth.can_view_batches')
def index(request):
    indicators = Indicator.objects.all()
    indicator_filter_form = IndicatorFilterForm(data=request.GET)
    indicators = _process_form(indicator_filter_form, indicators)

    return render(request, 'indicator/index.html',
                  {'indicators': indicators, 'indicator_filter_form': indicator_filter_form})


@permission_required('auth.can_view_batches')
def delete(request, indicator_id):
    indicator = Indicator.objects.get(id=indicator_id)
    indicator.indicator_criteria.all().delete()
    indicator.delete()
    messages.success(request, 'Indicator successfully deleted.')
    return HttpResponseRedirect('/indicators/')


def edit(request, indicator_id):
    indicator = Indicator.objects.get(id=indicator_id)
    indicator_form = IndicatorForm(instance=indicator)
    if request.method == 'POST':
        indicator_form = IndicatorForm(data=request.POST, instance=indicator)
        if indicator_form.is_valid():
            indicator_form.save()
            messages.success(request, "Indicator successfully edited.")
            return HttpResponseRedirect("/indicators/")
        messages.error(request, "Indicator was not successfully edited.")
    request.breadcrumbs([
        ('Indicators', reverse('list_indicator_page')),
    ])
    context = {'indicator_form': indicator_form, 'title': 'Edit Indicator',
               'button_label': 'Save', 'cancel_url': reverse('list_indicator_page')}
    return render(request, 'indicator/new.html', context)


@permission_required('auth.can_view_household_groups')
def add_indicator_variable(request, indicator_id):
    response = None
    indicator = Indicator.get(pk=indicator_id)
    variable_form = IndicatorVariableForm(indicator)
    if request.method == 'POST':
        variable_form = IndicatorVariableForm(indicator, data=request.POST)
        if variable_form.is_valid():
            variable = variable_form.save()
            messages.success(request, 'Variable successfully saved.')
            return HttpResponseRedirect(reverse('edit_indicator_variable', args=(variable.pk, )))
    context = {'variable_form': variable_form,
               'indicator': indicator,
               'title': "Manage Indicator Criteria",
               'button_label': 'Save',
               'id': 'add_group_form',
               'cancel_url': reverse('list_indicator_page'),
               'parameter_questions': indicator.batch.all_questions,
               'condition_title': "Conditions"}
    request.breadcrumbs([
        ('Indicators', reverse('list_indicator_page')),
        ('Variable List', reverse('view_indicator_variables', args=(indicator_id, ))),
    ])
    return response or render(request, 'indicator/indicator_variable.html', context)


@permission_required('auth.can_view_household_groups')
def edit_indicator_variable(request, variable_id):
    response = None
    variable = IndicatorVariable.get(id=variable_id)
    variable_form = IndicatorVariableForm(variable.indicator, instance=variable)
    if request.method == 'POST':
        variable_form = IndicatorVariableForm(variable.indicator, instance=variable, data=request.POST)
        if variable_form.is_valid():
            variable_form.save()
            messages.success(request, 'Variable successfully saved.')
            return HttpResponseRedirect(reverse('edit_indicator_variable', args=(variable.pk, )))
    context = {'variable_form': variable_form,
               'indicator': variable.indicator,
               'title': "Manage Indicator Criteria",
               'button_label': 'Save',
               'id': 'add_group_form',
               'cancel_url': reverse('list_indicator_page'),
               'parameter_questions': variable.indicator.batch.all_questions,
               'conditions': variable.criteria.all(),
               'condition_title': "Conditions"}
    request.breadcrumbs([
        ('Indicators', reverse('list_indicator_page')),
        ('Variable List', reverse('view_indicator_variables', args=(variable.indicator.pk, ))),

    ])
    return response or render(request, 'indicator/indicator_variable.html', context)


@permission_required('auth.can_view_household_groups')
def delete_indicator_variable(request, variable_id):
    get_object_or_404(IndicatorVariable, id=variable_id).delete()
    messages.info(request, 'Variable removed successfully')
    return HttpResponseRedirect(reverse('list_indicator_page'))


@permission_required('auth.can_view_household_groups')
def delete_indicator_criteria(request, indicator_criteria_id):
    criterion = get_object_or_404(IndicatorVariableCriteria, id=indicator_criteria_id)
    variable = criterion.variable
    criterion.delete()
    messages.info(request, 'condition removed successfully')
    return HttpResponseRedirect(reverse('edit_indicator_variable', args=(variable.pk, )))


def view_indicator_variables(request, indicator_id):
    indicator = get_object_or_404(Indicator, id=indicator_id)
    request.breadcrumbs([
        ('Indicators', reverse('list_indicator_page')),
    ])
    context = {'indicator': indicator, 'variables': indicator.variables.all()}
    return render(request, 'indicator/indicator_variable_list.html', context)


@login_required
def variables(request):
    id = request.GET.get('id', None)
    # return questions before last question
    indicator = Indicator.get(pk=id)
    json_dump = json.dumps(list(indicator.variables.values_list('name', )))
    return HttpResponse(json_dump, content_type='application/json')


def add_indicator_formular(request, indicator_id):
    return HttpResponseRedirect('../')


@permission_required('auth.can_view_batches')
def simple_indicator(request, indicator_id):
    hierarchy_limit = 2
    selected_location = Location.objects.get(parent__isnull=True)
    params = request.GET or request.POST
    locations_filter = LocationsFilterForm(data=params)
    indicator_metric_form = IndicatorMetricFilterForm(params)
    metric = int(indicator_metric_form.data.get('metric', Indicator.COUNT))
    first_level_location_analyzed = Location.objects.filter(
        type__name__iexact="country")[0]
    indicator = Indicator.objects.get(id=indicator_id)
    formula = indicator.indicator_criteria.all()
    request.breadcrumbs([
        ('Indicator List', reverse('list_indicator_page')),
    ])
    if locations_filter.last_location_selected:
        selected_location = locations_filter.last_location_selected
        # hence set the location where the report is based. i.e the child current selected location.
    context = {'request': request,
               'reports': indicator.get_data(selected_location.get_children().order_by('name'), metric, _presenter),
               'indicator': indicator,
               'locations_filter': locations_filter,
               'options': indicator.parameter.options.order_by('order'),
               'selected_location': selected_location,
               'indicator_metric_form': indicator_metric_form,
               'metric': 'Count' if metric == Indicator.COUNT else 'Percentage'
               }
    return render(request, 'indicator/simple_indicator.html', context)


def _presenter(tabulated_data, child_location, loc_answers, options, factor):
    tabulated_data[child_location.name] = [loc_answers.filter(value__pk=option.pk).count()*factor
                                               for option in options]
