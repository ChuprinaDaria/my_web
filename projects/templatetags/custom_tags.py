# projects/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def getattr(obj, attr_name):
    return getattr(obj, attr_name, '')
