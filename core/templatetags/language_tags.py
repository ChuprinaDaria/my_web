from django import template
from django.utils.translation import get_language
import re

register = template.Library()

@register.filter
def remove_language_prefix(path):
    """
    Видаляє мовний префікс з початку URL шляху
    /uk/about/ -> /about/
    /pl/projects/ -> /projects/
    /en/contacts/ -> /contacts/
    /about/ -> /about/ (без змін)
    """
    if not path:
        return path
    
    # Регулярний вираз для видалення мовного префіксу тільки з початку
    pattern = r'^/(uk|pl|en)/'
    
    # Якщо знайдено мовний префікс на початку, видаляємо його
    if re.match(pattern, path):
        return re.sub(pattern, '/', path)
    
    return path
