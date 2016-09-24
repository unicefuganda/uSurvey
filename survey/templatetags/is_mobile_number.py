from django import template

register = template.Library()


@register.filter
def is_mobile_number(field):
    return 'mobile number' in field.lower()
