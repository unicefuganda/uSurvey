from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from survey.forms.indicator import IndicatorForm
from survey.models import Indicator


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
    return render(request, 'indicator/index.html', {'indicators': indicators})