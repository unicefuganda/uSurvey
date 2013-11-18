from django import template
from django.contrib import messages
import json
register = template.Library()

@register.filter
def title_for_barchart(formula, locations):
    title = "%s for %s" % (formula.indicator.name, title_for_location_type(locations))
    return title

@register.filter
def location_names(hierarchial_data):
    names = [str(location.name) for location in hierarchial_data.keys()]
    return names

@register.filter
def title_for_location_type(locations):
    next_type_in_hierarchy = locations.next_type_in_hierarchy()
    if next_type_in_hierarchy:
        return next_type_in_hierarchy.name

@register.filter
def get_values(hierarchial_data):
    return hierarchial_data.values()

@register.filter
def is_float(value):
    return type(value) == float

@register.filter
def can_display_location_based_chart(locations):
    return title_for_location_type(locations) != None

@register.filter
def household_names(households):
    names = [str(household.get_head().surname) for household in households.keys()]
    return names

@register.filter
def get_numerator_denominator_values(households_data, formula):
    aggregated_data = { formula.numerator.text: [], formula.denominator.text: []}
    for household, answers in households_data.items():
        for question, answer in answers.items():
            aggregated_data[question.text].append(answer)
    result = []
    for name, data in aggregated_data.items():
        result.append({
            'name': str(name),
            'data': data
        })
    return result

@register.filter
def multi_choice_options(computed_value):
    return [str(key) for key in computed_value.keys()]

@register.filter
def get_computational_value_by_answer(hierarchial_data):
    options = {}
    for location, answers in hierarchial_data.items():
        for option, answer in answers.items():
            if not options.has_key(option):
                options[option] = []
            options[option].append(answer)
    data = []
    for key, value in options.items():
        data.append({
            'name': str(key),
            'data': value
        })
    return data

@register.filter
def get_numerator(answer, formula):
    return answer[formula.numerator].text

@register.filter
def get_denominator(answer, formula):
    return answer[formula.denominator]