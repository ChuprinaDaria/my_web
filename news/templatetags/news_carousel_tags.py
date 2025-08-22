from django import template
from django.db.models import Q
from news.models import ProcessedArticle

register = template.Library()

@register.inclusion_tag('includes/news_carousel.html', takes_context=True)
def news_carousel(context, filter_tags=None, limit=6, title=None, show_navigation=True):
    """Карусель новин"""
    
    current_lang = context.get('CURRENT_LANG', 'uk')
    
    queryset = ProcessedArticle.objects.filter(status='published')
    
    # Фільтри по тегах (використовуємо існуючу систему тегів)
    if filter_tags:
        tags = [tag.strip() for tag in filter_tags.split(',')]
        filters = Q()
        
        for tag in tags:
            if tag == 'top':
                filters |= Q(is_top_article=True)
            elif tag == 'fresh':
                # Свіжі статті (менше тижня)
                from django.utils import timezone
                from datetime import timedelta
                week_ago = timezone.now() - timedelta(days=7)
                filters |= Q(published_at__gte=week_ago)
            else:
                # Пошук по тегах через систему тегів
                try:
                    from core.models import Tag
                    tag_obj = Tag.objects.filter(slug=tag).first()
                    if tag_obj:
                        filters |= Q(tags=tag_obj)
                except:
                    pass
        
        if filters:
            queryset = queryset.filter(filters)
    
    articles = queryset.order_by('-published_at')[:limit]
    
    return {
        'articles': articles,
        'title': title or 'Новини',
        'show_navigation': show_navigation,
        'carousel_id': f"news_{filter_tags or 'all'}",
        'CURRENT_LANG': current_lang,
    }