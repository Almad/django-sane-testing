from django import template

register = template.Library()

@register.filter
def ihatebs(value):
    return value.replace('b', 'a')
