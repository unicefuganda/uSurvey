from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from survey.forms.indicator import IndicatorForm
from survey.forms.filters import IndicatorFilterForm
from survey.models import Indicator, Survey


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
    return render(request, 'indicator/new.html',
                  {'indicator_form': indicator_form, 'title': 'Add Indicator', 'button_label': 'Save',
                   'action': '/indicators/new/'})


@permission_required('auth.can_view_batches')
def index(request):
    indicators = Indicator.objects.all()
    indicator_filter_form = IndicatorFilterForm()
    if request.method == 'POST':
        indicator_filter_form = IndicatorFilterForm(request.POST)
        if indicator_filter_form.is_valid():
            survey_id = indicator_filter_form.cleaned_data['survey']
            batch_id = indicator_filter_form.cleaned_data['batch']
            if batch_id.isdigit():
                print 'haha'
                print [i.batch.id for i in indicators]
                print batch_id
                indicators = indicators.filter(batch=batch_id)
                print indicators
            elif survey_id.isdigit():
                batches = Survey.objects.get(id=survey_id).batch.all()
                indicators = indicators.filter(batch__in=batches)

    return render(request, 'indicator/index.html',
                  {'indicators': indicators, 'indicator_filter_form': indicator_filter_form})