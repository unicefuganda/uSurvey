from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from rapidsms.contrib.locations.models import Location
from django.contrib.auth.decorators import login_required, permission_required
from survey.forms.formula import FormulaForm
from survey.models import Indicator, Question
from survey.models.formula import Formula
from survey.views.location_widget import LocationWidget
from survey.views.views_helper import contains_key

@login_required
@permission_required('auth.can_view_aggregates')
def show(request, batch_id, formula_id):
    params = request.GET
    computed_value = None
    hierarchial_data = None
    household_data = None
    weights = None
    selected_location = Location.objects.get(id=params['location']) if contains_key(params, 'location') else None
    formula = Formula.objects.get(id=formula_id)
    if selected_location:
        computed_value = formula.compute_for_location(selected_location)
        hierarchial_data = formula.compute_for_next_location_type_in_the_hierarchy(current_location=selected_location)
        weights = formula.weight_for_location(selected_location)
        household_data = formula.compute_for_households_in_location(selected_location)
    return render(request, 'formula/show.html', {   'request': request,
                                                    'locations': LocationWidget(selected_location),
                                                    'computed_value': computed_value,
                                                    'hierarchial_data': hierarchial_data,
                                                    'household_data': household_data,
                                                    'weights': weights,
                                                    'formula': formula,
                                                    'batch_id': batch_id,
                                                })

def _process_new_request(request, formula_form, new_formula_url, indicator):
    if formula_form.is_valid():
        if indicator.is_percentage_indicator():
            denominator_question = formula_form.cleaned_data['denominator']
            numerator_question = formula_form.cleaned_data['numerator']
            Formula.objects.create(numerator=numerator_question, denominator=denominator_question, indicator=indicator)
        else:
            count_question = formula_form.cleaned_data['count']
            Formula.objects.create(count=count_question, indicator=indicator)

        success_message = "Formula successfully added to indicator %s." % indicator.name
        messages.success(request, success_message)
        return HttpResponseRedirect(new_formula_url)

def new(request, indicator_id):
    try:
        indicator = Indicator.objects.get(id=indicator_id)
        formula_form = FormulaForm(indicator=indicator)
        new_formula_url = '/indicators/%s/formula/new/' % indicator_id

        if request.method == 'POST':
            formula_form = FormulaForm(indicator=indicator, data=request.POST)
            _process_new_request(request, formula_form, new_formula_url, indicator)

        form_title = 'Formula for Indicator %s' % indicator.name
        return render(request, 'formula/new.html', {'action': new_formula_url,
                                                    'cancel_url': '/indicators/', 'formula_form': formula_form,
                                                    'button_label': 'Create', 'title': form_title,
                                                    'existing_formula': indicator.formula.all(),
                                                    'indicator': indicator})
    except Indicator.DoesNotExist:
        error_message = "The indicator requested does not exist."
        messages.error(request, error_message)
        return HttpResponseRedirect("/indicators/")

def delete(request, indicator_id, formula_id):
    try:
        formula = Formula.objects.get(id=formula_id)
        formula.delete()
        messages.success(request, "Formula successfully deleted.")
    except Formula.DoesNotExist:
        messages.error(request, "Formula for indicator does not exist.")

    redirect_url = '/indicators/%s/formula/new/' % indicator_id
    return HttpResponseRedirect(redirect_url)