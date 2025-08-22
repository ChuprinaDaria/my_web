from django import template
from django.db.models import Q
from projects.models import Project

register = template.Library()

@register.inclusion_tag('includes/projects_carousel.html', takes_context=True)
def projects_carousel(context, filter_tags=None, limit=6, title=None, show_navigation=True):
    """
    Карусель проєктів
    {% projects_carousel filter_tags='ai,automation' limit=5 title="AI Projects" %}
    """
    
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
    
    projects = queryset.order_by('-priority', '-project_date')[:limit]
    
    return {
        'projects': projects,
        'title': title or 'Проєкти',
        'show_navigation': show_navigation,
        'carousel_id': f"projects_{filter_tags or 'all'}",
        'CURRENT_LANG': current_lang,
    }

@register.inclusion_tag('includes/projects_carousel.html', takes_context=True) 
def featured_projects(context, limit=4):
    """Топові проєкти"""
    return projects_carousel(
        context,
        filter_tags='top,ai',
        limit=limit,
        title='Рекомендовані проєкти'
    )

@register.inclusion_tag('includes/projects_carousel.html', takes_context=True)
def related_projects_by_tags(context, article, limit=4):
    """Проєкти по тегах статті"""
    if not hasattr(article, 'tags') or not article.tags.exists():
        return projects_carousel(context, limit=limit, title='Схожі проєкти')
    
    # Отримуємо теги статті і шукаємо проєкти
    article_tags = article.tags.all().values_list('slug', flat=True)
    
    # Мапінг тегів статей на фільтри проєктів
    project_filters = []
    for tag_slug in article_tags:
        if 'ai' in tag_slug or 'машинне' in tag_slug:
            project_filters.append('ai')
        elif 'automation' in tag_slug or 'автоматизація' in tag_slug:
            project_filters.append('automation')
        elif 'enterprise' in tag_slug or 'корпоративн' in tag_slug:
            project_filters.append('enterprise')
    
    filter_string = ','.join(project_filters) if project_filters else 'top'
    
    return projects_carousel(
        context,
        filter_tags=filter_string,
        limit=limit,
        title='Схожі проєкти'
    )