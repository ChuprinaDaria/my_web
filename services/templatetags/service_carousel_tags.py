from django import template
from django.db import models
from django.utils.translation import get_language
from services.models import ServiceCategory

register = template.Library()

@register.inclusion_tag('includes/simple_service_carousel.html', takes_context=True)
def services_carousel(context, limit=6, title=None, section_id="default", show_view_all=True):
    request = context.get('request')
    lang = get_language() or 'uk'
    
    services = ServiceCategory.objects.prefetch_related('tags').order_by('-priority', '-date_created')[:limit]
    
    services_data = []
    for service in services:
        services_data.append({
            'slug': service.slug,
            'title': service.get_title(lang),
            'short': service.get_short(lang),
            'icon': service.icon,
            'priority': getattr(service, 'priority', 2),
            'is_featured': getattr(service, 'is_featured', False),
            'projects_count': 0,  # ServiceCategory не має projects_count
            'tags': service.tags.filter(is_active=True)[:3] if hasattr(service, 'tags') else [],
        })
    
    return {
        'services': services_data,
        'title': title,
        'section_id': section_id,
        'show_view_all': show_view_all,
        'request': request,
        'lang': lang,
    }