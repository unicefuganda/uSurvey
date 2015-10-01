from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from survey.forms.indicator import IndicatorForm
from survey.forms.filters import IndicatorFilterForm
from survey.models import Indicator, Survey, Formula


@permission_required('auth.can_view_batches')
def new(request):
    indicator_form = IndicatorForm()
    if request.method == 'POST':
        indicator_form = IndicatorForm(request.POST)
        if indicator_form.is_valid():
            indicator_form.save()
            messages.success(request, "Indicator successfully created.")
            return HttpResponseRedirect("/indicators/")
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
            indicators = indicators.filter(batch=batch_id)
        elif survey_id.isdigit():
            batches = Survey.objects.get(id=survey_id).batches.all()
            indicators = indicators.filter(batch__in=batches)
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
    Formula.objects.filter(indicator=indicator).delete()
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
    context = {'indicator_form': indicator_form, 'title': 'Edit Indicator', 'button_label': 'Save', 'cancel_url': reverse('list_indicator_page')}
    return render(request, 'indicator/new.html', context)

