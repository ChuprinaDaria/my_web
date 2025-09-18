from django import template
from django.utils.translation import get_language

register = template.Library()

@register.simple_tag
def get_localized_title(article):
    """Отримати заголовок статті для поточної мови"""
    current_lang = get_language()
    return article.get_title(current_lang)

@register.simple_tag
def get_localized_summary(article):
    """Отримати короткий опис статті для поточної мови"""
    current_lang = get_language()
    return article.get_summary(current_lang)

@register.simple_tag
def get_localized_category_name(category):
    """Отримати назву категорії для поточної мови"""
    current_lang = get_language()
    return category.get_name(current_lang)
