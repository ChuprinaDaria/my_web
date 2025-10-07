from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from django.core.paginator import Paginator
from .models import ServiceCategory, FAQ, ServiceOverview
from projects.models import Project
from news.models import ProcessedArticle

def get_localized_field(obj, field_name, lang):
    """Helper для отримання локалізованого поля"""
    return getattr(obj, f"{field_name}_{lang}", 
           getattr(obj, f"{field_name}_en", 
           getattr(obj, field_name, "")))

def services_list(request):
    lang = get_language()
    # Показуємо всі сервіси (включаючи всі featured) на сторінці services_list
    items = ServiceCategory.objects.select_related().prefetch_related('tags').order_by('-priority', '-order', '-date_created')
    services = []
    
    for s in items:
        services.append({
            "slug": s.slug,
            "title": s.get_title(lang),
            "short": s.get_short(lang),
            "is_featured": s.is_featured,
            "priority_emoji": s.get_priority_emoji(),
            "icon": s.icon.url if s.icon else None,
            "main_image": s.main_image.url if s.main_image else None,
            "tags": s.tags.filter(is_active=True)[:3],  # Тільки 3 теги
        })
    
    # Отримуємо пов'язані проєкти
    related_projects = Project.objects.filter(
        is_active=True
    ).select_related('category').prefetch_related('tags').order_by(
        '-priority', '-project_date'
    )[:5]  # Тільки 5 проєктів для sidebar
    
    # Локалізуємо проєкти
    localized_projects = []
    for project in related_projects:
        localized_projects.append({
            "slug": project.slug,
            "title_en": project.title_en,
            "title_uk": project.title_uk,
            "title_pl": project.title_pl,
            "short_description_en": project.short_description_en,
            "short_description_uk": project.short_description_uk,
            "short_description_pl": project.short_description_pl,
            "featured_image": project.featured_image,
            "url": project.get_absolute_url(lang) if hasattr(project, 'get_absolute_url') else f'/{lang}/projects/{project.slug}/',
        })
    
    faqs = FAQ.objects.filter(is_active=True).order_by("order")
    localized_faqs = [
        {
            "question": get_localized_field(f, "question", lang),
            "answer": get_localized_field(f, "answer", lang),
        }
        for f in faqs
    ]
    
    # Отримуємо ServiceOverview для hero секції
    service_overview = ServiceOverview.objects.first()
    overview_title = None
    overview_description = None
    
    if service_overview:
        overview_title = get_localized_field(service_overview, "title", lang)
        overview_description = get_localized_field(service_overview, "description", lang)
    
    # Отримуємо останні статті для projects_news_section
    latest_articles = ProcessedArticle.objects.filter(
        status='published'
    ).order_by('-published_at')[:3]  # Тільки 3 останні статті
    
    # Локалізуємо статті
    related_articles = []
    for article in latest_articles:
        related_articles.append({
            "title_en": getattr(article, 'title_en', ''),
            "title_uk": getattr(article, 'title_uk', ''),
            "title_pl": getattr(article, 'title_pl', ''),
            "summary": get_localized_field(article, "summary", lang),
            "url": article.get_absolute_url(lang) if hasattr(article, 'get_absolute_url') else '#',
            "featured_image": article.ai_image_url,
            "published_at": article.published_at,
            "category": getattr(article, 'category', None),
        })
    
    # Отримуємо daily_digest для news section
    daily_digest_articles = ProcessedArticle.objects.filter(
        status='published'
    ).order_by('-published_at')[:5]  # 5 статей для daily digest
    
    # Локалізуємо daily_digest
    daily_digest = []
    for article in daily_digest_articles:
        daily_digest.append({
            "title_en": getattr(article, 'title_en', ''),
            "title_uk": getattr(article, 'title_uk', ''),
            "title_pl": getattr(article, 'title_pl', ''),
            "published_at": article.published_at,
            "category": getattr(article, 'category', None),
            "get_absolute_url": article.get_absolute_url(lang) if hasattr(article, 'get_absolute_url') else '#',
        })

    return render(request, "services/services_list.html", {
        "services": services, 
        "faqs": localized_faqs,
        "related_projects": localized_projects,
        "related_articles": related_articles,
        "daily_digest": daily_digest,
        "overview_title": overview_title,
        "overview_description": overview_description,
        "lang": lang,
        "debug_faqs": localized_faqs
    })

def service_detail(request, slug):
    lang = get_language()
    
    # Отримуємо ServiceCategory з тегами
    service_category = get_object_or_404(
        ServiceCategory.objects.prefetch_related('tags'), 
        slug=slug
    )
    
    # 🚀 ПРОЄКТИ з цієї категорії - ВИПРАВЛЕНО!
    projects_qs = Project.objects.filter(
        is_active=True, 
        category=service_category  # ← Правильно! category це ServiceCategory
    ).select_related('category').prefetch_related('tags').order_by('-priority', '-project_date')[:6]
    
    # Формуємо дані проєктів для шаблону
    related_projects = []
    for p in projects_qs:
        related_projects.append({
            "slug": p.slug,
            "title": get_localized_field(p, "title", lang),
            "short_description": get_localized_field(p, "short_description", lang),
            "featured_image": p.featured_image,
            "all_badges": p.get_all_badges(lang) if hasattr(p, 'get_all_badges') else [],
            "priority": getattr(p, 'priority', 0),
            "project_date": getattr(p, 'project_date', None),
        })
    
    # 📰 ПОВ'ЯЗАНІ НОВИНИ через теги (якщо є)
    related_articles = []
    if service_category.tags.exists():
        try:
            from news.models import ProcessedArticle
            articles_qs = ProcessedArticle.objects.filter(
                status='published',
                tags__in=service_category.tags.all()
            ).distinct().order_by('-published_at')[:3]
            
            for article in articles_qs:
                related_articles.append({
                    'title': article.get_title(lang) if hasattr(article, 'get_title') else getattr(article, 'title', ''),
                    'url': article.get_absolute_url() if hasattr(article, 'get_absolute_url') else '#',
                    'ai_image_url': getattr(article, 'ai_image_url', None),
                    'published_at': getattr(article, 'published_at', None),
                    'source_domain': getattr(article, 'source_domain', ''),
                })
        except ImportError:
            print("⚠️  News app не доступний")
            pass
    
    # 🔗 КРОС-ПРОМОЦІЯ контенту (комбінована)
    cross_promotion_content = []
    
    # Додаємо новини в крос-промоцію
    for article in related_articles:
        cross_promotion_content.append({
            'type': 'article',
            'title': article['title'],
            'summary': 'Цікаві інсайти та новини...',  # Можна додати summary якщо є
            'url': article['url'],
            'image': article['ai_image_url'],
        })
    
    # Додаємо проєкти в крос-промоцію
    for project in related_projects[:3]:  # Беремо тільки 3 топових
        cross_promotion_content.append({
            'type': 'project',
            'title': project['title'],
            'summary': project['short_description'][:100] + '...' if project['short_description'] else 'Детальний опис проєкту...',
            'url': f'/{lang}/projects/{project["slug"]}/',
            'image': project['featured_image'].url if project['featured_image'] else None,
        })
    
    # Галерея зображень
    gallery = [img for img in [
        service_category.gallery_image_1,
        service_category.gallery_image_2,
        service_category.gallery_image_3,
        service_category.gallery_image_4
    ] if img]
    
    # 📊 Формуємо дані сервісу для шаблону
    service_data = {
        "slug": service_category.slug,
        "title": service_category.get_title(lang),
        "seo_title": service_category.get_seo_title(lang),
        "seo_description": service_category.get_seo_desc(lang),
        "long_description": service_category.get_desc(lang),
        "short": service_category.get_short(lang),
        "audience": service_category.get_audience(lang),
        "pricing": service_category.get_pricing(lang),
        "value": service_category.get_value(lang),
        "video_url": service_category.video_url,
        "video_file": service_category.video_file.url if service_category.video_file else None,
        "gallery": gallery,
        "main_image": service_category.main_image,
        "priority_emoji": service_category.get_priority_emoji(),
        "is_featured": service_category.is_featured,
        "icon": service_category.icon.url if service_category.icon else None,
        "date_created": service_category.date_created,
        "priority": service_category.priority,
        "related_projects_count": len(related_projects),
        "related_articles_count": len(related_articles),
        "tags": service_category.tags.filter(is_active=True)[:3],  # Тільки 3 теги
    }
    
    print(f"🎯 Service '{service_data['title']}': {len(related_projects)} проєктів, {len(related_articles)} новин")
    
    # OG-теги для соцмереж
    og_title = service_data['title']
    og_description = service_data['short'][:200] if service_data.get('short') else ''
    og_image_url = None

    # Перевіряємо чи є og_image
    if hasattr(service_category, 'og_image') and service_category.og_image:
        og_image_url = request.build_absolute_uri(service_category.og_image.url)
    # Якщо немає og_image, використовуємо main_image
    elif service_category.main_image:
        og_image_url = request.build_absolute_uri(service_category.main_image.url)
    # Або icon як fallback
    elif service_category.icon:
        og_image_url = request.build_absolute_uri(service_category.icon.url)
    
    return render(request, "services/service_detail.html", {
        "service": service_data,
        "related_projects": related_projects,
        "related_articles": related_articles,
        "cross_promotion_content": cross_promotion_content,
        "lang": lang,
        # OG-теги для соцмереж
        "og_title": og_title,
        "og_description": og_description,
        "og_image": og_image_url,
        "og_url": request.build_absolute_uri(),
    })

def faq_list(request):
    """FAQ сторінка"""
    lang = get_language()
    
    # Отримуємо всі FAQ
    faqs = FAQ.objects.filter(is_active=True).order_by('order')
    
    # Локалізуємо FAQ
    localized_faqs = [
        {
            'question': get_localized_field(faq, 'question', lang),
            'answer': get_localized_field(faq, 'answer', lang),
        }
        for faq in faqs
    ]
    
    return render(request, "services/faq.html", {
        "faqs": localized_faqs,
        "lang": lang,
    })