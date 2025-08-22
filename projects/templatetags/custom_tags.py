# projects/templatetags/custom_tags.py
from django import template
from django.db.models import Q

register = template.Library()

@register.filter
def getattr(obj, attr_name):
    return getattr(obj, attr_name, '')

@register.inclusion_tag('includes/projects_carousel.html', takes_context=True)
def projects_carousel(context, filter_tags=None, limit=6, title=None, show_navigation=True):
    """Карусель проєктів"""
    
    try:
        from projects.models import Project
        current_lang = context.get('CURRENT_LANG', 'uk')
        
        queryset = Project.objects.filter(is_active=True)
        
        # Фільтри по тегах
        if filter_tags:
            tags = [tag.strip() for tag in filter_tags.split(',')]
            filters = Q()
            
            for tag in tags:
                if tag == 'top':
                    filters |= Q(is_top_project=True)
                elif tag == 'ai':
                    filters |= Q(is_ai_powered=True)
                elif tag == 'automation':
                    filters |= Q(project_type_uk__icontains='автоматизація') | Q(project_type_en__icontains='automation')
                elif tag == 'innovative':
                    filters |= Q(is_innovative=True)
                elif tag == 'enterprise':
                    filters |= Q(is_enterprise=True)
                elif tag == 'complex':
                    filters |= Q(is_complex=True)
            
            if filters:
                queryset = queryset.filter(filters)
        
        projects = list(queryset.order_by('-priority', '-project_date')[:limit])
        
    except Exception as e:
        projects = []
    
    return {
        'projects': projects,
        'title': title or 'Проєкти',
        'show_navigation': show_navigation,
        'carousel_id': f"projects_{filter_tags or 'all'}",
        'CURRENT_LANG': context.get('CURRENT_LANG', 'uk'),
    }