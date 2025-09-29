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
        return '/'
    
    # Забезпечуємо, що path починається з /
    if not path.startswith('/'):
        path = '/' + path
    
    # Регулярний вираз для видалення мовного префіксу тільки з початку
    # Включаємо випадки /uk, /uk/, /pl, /pl/, /en, /en/
    pattern = r'^/(uk|pl|en)(/|$)'
    
    # Якщо знайдено мовний префікс на початку, видаляємо його
    match = re.match(pattern, path)
    if match:
        # Видаляємо префікс, залишаючи початковий /
        result = re.sub(pattern, '/', path)
        # Якщо результат порожній або тільки /, повертаємо /
        return result if result != '' else '/'
    
    return path


@register.filter
def add_language_prefix(path, lang):
    """
    Додає мовний префікс до URL шляху
    ('/about/', 'uk') -> '/uk/about/'
    ('/about/', 'en') -> '/about/' (для англійської без префікса)
    """
    if not path:
        path = '/'
    
    # Забезпечуємо, що path починається з /
    if not path.startswith('/'):
        path = '/' + path
    
    # Для англійської мови (default) не додаємо префікс
    if lang == 'en':
        return path
    
    # Для інших мов додаємо префікс
    return f'/{lang}{path}'
