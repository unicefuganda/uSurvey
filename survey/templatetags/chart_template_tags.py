from django import template

register = template.Library()

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