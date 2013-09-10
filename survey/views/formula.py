from django.shortcuts import render
from rapidsms.contrib.locations.models import Location
from django.contrib.auth.decorators import login_required, permission_required
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
    formula = Formula.objects.get(batch_id=batch_id, id=formula_id)
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
                                                })