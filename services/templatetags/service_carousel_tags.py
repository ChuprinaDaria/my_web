# services/templatetags/service_carousel_tags.py
from django import template
from django.db.models import Q
from services.models import Service

register = template.Library()

@register.inclusion_tag('includes/service_carousel.html', takes_context=True)
def services_carousel(context, filter_tags=None, limit=6, title=None,
                      section_id="services", auto_play=True, auto_play_interval=5000,
                      show_view_all=True):
    """Карусель сервісів з тегами"""

    current_lang = context.get('CURRENT_LANG', 'uk')

    # 🔧 ВИПРАВЛЕНО: Додано prefetch_related('tags')
    qs = Service.objects.filter(is_active=True).prefetch_related('tags').order_by('-is_featured', '-priority', '-date_created')

    # Примітивний фільтр по назві (поки без моделі Tag)
    if filter_tags:
        tags = [t.strip() for t in filter_tags.split(',') if t.strip()]
        f = Q()
        for t in tags:
            if t == 'ai':
                f |= Q(title_uk__icontains='AI') | Q(title_en__icontains='AI')
            elif t == 'automation':
                f |= Q(title_uk__icontains='автоматиза') | Q(title_en__icontains='automati')
            elif t == 'crm':
                f |= Q(title_uk__icontains='CRM') | Q(title_en__icontains='CRM')
            elif t == 'ecommerce':
                f |= Q(title_uk__icontains='магаз') | Q(title_en__icontains='ecomm')
        if f:
            qs = qs.filter(f)

    services = qs[:limit]
    
    # 🆕 ДОДАЄМО теги та метрики до кожного сервісу
    services_with_tags = []
    for service in services:
        # 🏷️ Отримуємо теги
        service_tags = service.tags.filter(is_active=True) if hasattr(service, 'tags') else []
        
        # 📊 Рахуємо крос-промо (спрощено)
        try:
            related_articles_count = service.get_related_articles().count() if hasattr(service, 'get_related_articles') else 0
        except:
            related_articles_count = 0
            
        try:
            related_projects_count = service.get_related_projects().count() if hasattr(service, 'get_related_projects') else 0
        except:
            related_projects_count = 0
        
        # Додаємо додаткові атрибути до сервісу
        service.tags_list = [
            {
                'name': getattr(tag, f'name_{current_lang}', getattr(tag, 'name_en', str(tag))),
                'emoji': getattr(tag, 'icon', '🏷️'),  # ВИПРАВЛЕНО: використовуємо 'icon' замість 'emoji'
                'color': getattr(tag, 'color', '#007bff')
            }
            for tag in service_tags[:2]  # Максимум 2 теги
        ]
        
        service.related_articles_count = related_articles_count
        service.related_projects_count = related_projects_count
        
        services_with_tags.append(service)

    return {
        'services': services_with_tags,
        'title': title or 'Our Services',
        'section_id': section_id,
        'auto_play': auto_play,
        'auto_play_interval': auto_play_interval,
        'show_view_all': show_view_all,
        'CURRENT_LANG': current_lang,
    }