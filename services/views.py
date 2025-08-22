from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from django.http import JsonResponse
from .models import Service, ServiceCategory, ServiceOverview, FAQ, ServiceFeature
from projects.models import Project


def services_list(request):
    """
    📋 Список сервісів з підтримкою нової системи тегів
    Готово до крос-промоції з новинами та проєктами
    """
    lang = get_language()

    overview = ServiceOverview.objects.first()

    # Оптимізовані запити з новими тегами
    categories = ServiceCategory.objects.prefetch_related(
        "services__tags",  # 🆕 Підтягуємо теги для сервісів
        "services",
        "projects__tags"   # 🆕 Підтягуємо теги для проєктів
    ).all()

    all_projects = list(Project.objects.filter(is_active=True))

    localized_categories = []
    for category in categories:
        # Фільтруємо та сортуємо сервіси з пріоритетом
        services = []
        for service in category.services.filter(is_active=True).order_by('-priority', '-order', '-date_created'):
            # 🏷️ НОВІ поля з тегами
            service_tags = list(service.tags.filter(is_active=True))

            # 🔗 Крос-промо: ФІКС для помилок методів
            try:
                related_articles = service.get_related_articles()
                related_articles_count = related_articles.count() if hasattr(related_articles, 'count') else len(related_articles)
            except (AttributeError, Exception):
                related_articles_count = 0

            try:
                related_projects = service.get_related_projects()
                related_projects_count = related_projects.count() if hasattr(related_projects, 'count') else len(related_projects)
            except (AttributeError, Exception):
                related_projects_count = 0

            # 🆕 ФІКС: Методи для пріоритету
            try:
                priority_emoji = service.get_priority_emoji()
            except (AttributeError, Exception):
                priority_emoji = "📋"

            services.append({
                "slug": service.slug,
                "icon": service.icon,
                "title": getattr(service, f"title_{lang}", service.title_en),
                "short_description": getattr(service, f"short_description_{lang}", service.short_description_en),

                # 🏷️ НОВІ теги (пріоритетні) - ФІКС для методів тегів
                "tags": [
                    {
                        'key': getattr(tag, 'key', f'tag_{tag.id}'),
                        'name': tag.get_name(lang) if hasattr(tag, 'get_name') else getattr(tag, f'name_{lang}', str(tag)),
                        'emoji': getattr(tag, 'emoji', '🏷️'),
                        'color': getattr(tag, 'color', '#007bff')
                    }
                    for tag in service_tags[:3]  # Максимум 3 теги для карток
                ],
                "tags_count": len(service_tags),

                # 🔗 НОВІ поля для крос-промоції
                "related_articles_count": related_articles_count,
                "related_projects_count": related_projects_count,

                # 📊 Нові метрики
                "priority": getattr(service, 'priority', 2),
                "priority_emoji": priority_emoji,
                "is_featured": getattr(service, 'is_featured', False),
            })

        # Існуючі проєкти (без змін)
        projects = [p for p in all_projects if p.category_id == category.id]
        localized_projects = []
        for project in projects:
            # 🏷️ ДОДАЄМО теги і для проєктів
            project_tags = list(project.tags.filter(is_active=True)) if hasattr(project, 'tags') else []

            localized_projects.append({
                "slug": project.slug,
                "title": getattr(project, f"title_{lang}", project.title_en),
                "short_description": getattr(project, f"short_description_{lang}", project.short_description_en),
                "featured_image": project.featured_image.url if project.featured_image else None,

                # 🏷️ НОВІ поля з тегами - ФІКС для методів тегів
                "tags": [
                    {
                        'key': getattr(tag, 'key', f'tag_{tag.id}'),
                        'name': tag.get_name(lang) if hasattr(tag, 'get_name') else getattr(tag, f'name_{lang}', str(tag)),
                        'emoji': getattr(tag, 'emoji', '🏷️'),
                        'color': getattr(tag, 'color', '#007bff')
                    }
                    for tag in project_tags[:2]  # 2 теги для проєктів
                ],
                "priority": getattr(project, 'priority', 2),
                "is_ai_powered": getattr(project, 'is_ai_powered', False),
            })

        localized_categories.append({
            "slug": category.slug,
            "title": getattr(category, f"title_{lang}", category.title_en),
            "description": getattr(category, f"description_{lang}", category.description_en),
            "services": services,
            "projects": localized_projects,

            # 🆕 НОВА статистика категорії
            "services_count": len(services),
            "projects_count": len(localized_projects),
        })

    # 🎯 Топ теги для фільтрування (НОВА функціональність) - ФІКС для помилок імпорту
    popular_tags_data = []
    try:
        from core.models import Tag
        popular_tags = Tag.get_popular_tags(limit=6) if hasattr(Tag, 'get_popular_tags') else Tag.objects.filter(is_active=True)[:6]
        popular_tags_data = [
            {
                'key': getattr(tag, 'key', f'tag_{tag.id}'),
                'name': tag.get_name(lang) if hasattr(tag, 'get_name') else getattr(tag, f'name_{lang}', str(tag)),
                'emoji': getattr(tag, 'emoji', '🏷️'),
                'color': getattr(tag, 'color', '#007bff'),
                'usage_count': getattr(tag, 'usage_count', 0)
            }
            for tag in popular_tags
        ]
    except (ImportError, AttributeError, Exception) as e:
        print(f"⚠️ Tags system error: {e}")
        popular_tags_data = []

    # Існуючі features та FAQs (без змін)
    features = [
        {
            "icon": f.icon,
            "title": getattr(f, f"title_{lang}", f.title_en)
        }
        for f in ServiceFeature.objects.filter(is_active=True).order_by("order")
    ]

    faqs = [
        {
            "question": getattr(f, f"question_{lang}", f.question_en),
            "answer": getattr(f, f"answer_{lang}", f.answer_en),
        }
        for f in FAQ.objects.filter(is_active=True).order_by("order")
    ]

    context = {
        # Існуючі поля (без змін)
        "overview_title": getattr(overview, f"title_{lang}", overview.title_en) if overview else "",
        "overview_description": getattr(overview, f"description_{lang}", overview.description_en) if overview else "",
        "seo_title": overview.seo_title if overview else "",
        "seo_description": overview.seo_description if overview else "",
        "og_image": overview.og_image.url if overview and overview.og_image else None,
        "categories": localized_categories,
        "features": features,
        "faqs": faqs,
        "lang": lang,

        # 🏷️ НОВІ дані для тегів та крос-промоції
        "popular_tags": popular_tags_data,
        "show_tag_filter": len(popular_tags_data) > 0,

        # 📊 НОВА статистика
        "total_services": sum(len(cat['services']) for cat in localized_categories),
        "total_projects": sum(len(cat['projects']) for cat in localized_categories),
        "featured_services": [
            service for cat in localized_categories
            for service in cat['services']
            if service.get('is_featured', False)
        ][:3],  # Топ 3 сервіси

        # 🆕 ДОДАЮ debug інформацію
        "debug": True,  # Для показу debug інформації
        "request": request,  # Для темплейтів
    }

    return render(request, "services/services_list.html", context)




def service_detail(request, slug):
    """
    📋 Детальна сторінка сервісу з крос-промоцією
    Показує пов'язані новини та проєкти через нову систему тегів
    """
    lang = get_language()
    
    # Оптимізований запит з тегами
    service = get_object_or_404(
        Service.objects.prefetch_related('tags'), 
        slug=slug, 
        is_active=True
    )

    # Існуючі дані сервісу (розширені) - ФІКС для помилок методів
    try:
        priority_emoji = service.get_priority_emoji()
    except (AttributeError, Exception):
        priority_emoji = "📋"

    try:
        priority_display = service.get_priority_display()
    except (AttributeError, Exception):
        priority_display = "Normal"

    service_data = {
        "slug": service.slug,
        "icon": service.icon,
        "title": getattr(service, f"title_{lang}", service.title_en),
        "short_description": getattr(service, f"short_description_{lang}", service.short_description_en),
        "description": getattr(service, f"description_{lang}", service.description_en),
        "seo_title": getattr(service, f"seo_title_{lang}", getattr(service, 'seo_title_en', '')),
        "seo_description": getattr(service, f"seo_description_{lang}", getattr(service, 'seo_description_en', '')),
        
        # 🆕 НОВІ поля
        "priority": getattr(service, 'priority', 2),
        "priority_emoji": priority_emoji,
        "priority_display": priority_display,
        "is_featured": getattr(service, 'is_featured', False),
        "order": getattr(service, 'order', 0),
    }

    # 🔗 НОВА крос-промоція через теги - ФІКС для помилок методів
    cross_promotion_content = []
    related_articles = []
    related_projects = []
    
    try:
        cross_promotion_content = service.get_cross_promotion_content(limit=6)
    except (AttributeError, Exception):
        cross_promotion_content = []

    try:
        related_articles = service.get_related_articles(limit=3)
    except (AttributeError, Exception):
        related_articles = []

    try:
        related_projects = service.get_related_projects(limit=3)
    except (AttributeError, Exception):
        related_projects = []
    
    # 🏷️ Теги сервісу
    service_tags = service.tags.filter(is_active=True)
    tags_data = []
    for tag in service_tags:
        try:
            tags_data.append({
                'key': getattr(tag, 'key', f'tag_{tag.id}'),
                'name': tag.get_name(lang) if hasattr(tag, 'get_name') else getattr(tag, f'name_{lang}', str(tag)),
                'emoji': getattr(tag, 'emoji', '🏷️'),
                'color': getattr(tag, 'color', '#007bff'),
                'description': getattr(tag, 'description', '')
            })
        except (AttributeError, Exception):
            # Fallback для простих тегів
            tags_data.append({
                'key': f'tag_{tag.id}',
                'name': str(tag),
                'emoji': '🏷️',
                'color': '#007bff',
                'description': ''
            })

    # 🎯 Рекомендації (сервіси з такими ж тегами) - ФІКС для помилок
    similar_services = []
    try:
        if service.tags.exists():
            first_tag = service.tags.first()
            similar_services = first_tag.services.filter(is_active=True).exclude(id=service.id)[:3]
        else:
            similar_services = []
    except (AttributeError, Exception):
        similar_services = []

    context = {
        # Існуючі поля
        "service": service_data,
        "lang": lang,
        "request": request,
        
        # 🏷️ НОВІ поля з тегами та крос-промоцією
        "service_tags": tags_data,
        "cross_promotion_content": cross_promotion_content,
        "related_articles": related_articles,
        "related_projects": related_projects,
        
        # 📊 Статистика для UI
        "show_cross_promotion": len(cross_promotion_content) > 0,
        "cross_stats": {
            'articles_count': len(related_articles) if hasattr(related_articles, '__len__') else (related_articles.count() if hasattr(related_articles, 'count') else 0),
            'projects_count': len(related_projects) if hasattr(related_projects, '__len__') else (related_projects.count() if hasattr(related_projects, 'count') else 0),
            'tags_count': len(tags_data)
        },
        
        # 🎯 Рекомендації
        "similar_services": similar_services,

        # 🆕 ДОДАЮ debug інформацію
        "debug": True,  # Для показу debug інформації
    }
    
    # 📊 Статистика для дебагу
    print(f"📋 Сервіс '{service_data['title']}': {len(tags_data)} тегів, "
          f"{len(related_articles)} новин, {len(related_projects)} проєктів")

    return render(request, "services/service_detail.html", context)


def faq_page(request):
    """FAQ сторінка (без змін, але з покращеннями)"""
    lang = get_language()

    faqs = FAQ.objects.filter(is_active=True).order_by("order")

    localized_faqs = [
        {
            "question": getattr(f, f"question_{lang}", f.question_en),
            "answer": getattr(f, f"answer_{lang}", f.answer_en),
        }
        for f in faqs
    ]

    context = {
        "faqs": localized_faqs,
        "lang": lang,
        "request": request,
        
        # 🆕 ДОДАТКОВА інформація
        "total_faqs": len(localized_faqs),
        "page_title": {
            "en": "Frequently Asked Questions",
            "uk": "Часті запитання",
            "pl": "Często zadawane pytania"
        }.get(lang, "FAQ"),
        
        # 🆕 ДОДАЮ debug
        "debug": True,
    }

    return render(request, "services/faq.html", context)


# 🆕 НОВІ views для фільтрування по тегам
def services_by_tag(request, tag_key):
    """
    🏷️ Фільтрування сервісів по тегу
    Нова функціональність для крос-навігації
    """
    try:
        from core.models import Tag
        tag = get_object_or_404(Tag, key=tag_key, is_active=True)
    except ImportError:
        return JsonResponse({'error': 'Tags system not available'}, status=404)
    
    lang = get_language()
    
    # Сервіси з цим тегом
    services = tag.services.filter(is_active=True).order_by('-priority', '-date_created')
    
    services_data = []
    for service in services:
        services_data.append({
            "slug": service.slug,
            "title": getattr(service, f"title_{lang}", service.title_en),
            "short_description": getattr(service, f"short_description_{lang}", service.short_description_en),
            "icon": service.icon.url if service.icon else None,
            "priority": getattr(service, 'priority', 2),
            "is_featured": getattr(service, 'is_featured', False),
        })
    
    # Пов'язаний контент - ФІКС для помилок методів
    related_articles = []
    related_projects = []
    
    try:
        related_articles = tag.get_related_articles(limit=3) if hasattr(tag, 'get_related_articles') else []
    except (AttributeError, Exception):
        related_articles = []

    try:
        related_projects = tag.get_related_projects(limit=3) if hasattr(tag, 'get_related_projects') else []
    except (AttributeError, Exception):
        related_projects = []
    
    context = {
        'tag': {
            'key': getattr(tag, 'key', f'tag_{tag.id}'),
            'name': tag.get_name(lang) if hasattr(tag, 'get_name') else str(tag),
            'emoji': getattr(tag, 'emoji', '🏷️'),
            'color': getattr(tag, 'color', '#007bff'),
            'description': getattr(tag, 'description', '')
        },
        'services': services_data,
        'related_articles': [
            {
                'title': article.get_title(lang) if hasattr(article, 'get_title') else str(article),
                'url': article.get_absolute_url() if hasattr(article, 'get_absolute_url') else '#',
                'published_at': article.published_at.isoformat() if hasattr(article, 'published_at') and article.published_at else None
            }
            for article in related_articles
        ],
        'related_projects': [
            {
                'title': getattr(project, f'title_{lang}', project.title_en),
                'url': f'/projects/{project.slug}/',
            }
            for project in related_projects
        ],
        'total_services': services.count(),
        'lang': lang
    }
    
    return JsonResponse(context)


def services_api(request):
    """
    🔌 API для сервісів з новою системою тегів
    """
    lang = get_language()
    services_data = []
    
    for service in Service.objects.filter(is_active=True).prefetch_related('tags'):
        # 🏷️ Додаємо теги до API - ФІКС для помилок
        service_tags = []
        try:
            for tag in service.tags.filter(is_active=True):
                service_tags.append({
                    'key': getattr(tag, 'key', f'tag_{tag.id}'),
                    'name_en': getattr(tag, 'name_en', str(tag)),
                    'name_uk': getattr(tag, 'name_uk', str(tag)),
                    'name_pl': getattr(tag, 'name_pl', str(tag)),
                    'emoji': getattr(tag, 'emoji', '🏷️'),
                    'color': getattr(tag, 'color', '#007bff')
                })
        except (AttributeError, Exception):
            service_tags = []

        # ФІКС для методів крос-промоції
        related_articles_count = 0
        related_projects_count = 0
        
        try:
            related_articles_count = service.get_related_articles().count()
        except (AttributeError, Exception):
            related_articles_count = 0

        try:
            related_projects_count = service.get_related_projects().count()
        except (AttributeError, Exception):
            related_projects_count = 0
        
        services_data.append({
            "title_en": service.title_en,
            "title_uk": getattr(service, 'title_uk', service.title_en),
            "title_pl": getattr(service, 'title_pl', service.title_en),
            "slug": service.slug,
            "priority": getattr(service, 'priority', 2),
            "is_featured": getattr(service, 'is_featured', False),
            "date_created": service.date_created.isoformat(),
            
            # 🏷️ НОВІ поля
            "tags": service_tags,
            "related_articles_count": related_articles_count,
            "related_projects_count": related_projects_count,
            
            # 📄 Контент
            "short_description": getattr(service, f"short_description_{lang}", service.short_description_en),
            "icon_url": service.icon.url if service.icon else None,
        })
    
    return JsonResponse({
        "services": services_data,
        "total_count": len(services_data),
        "api_version": "2.0_with_tags_fixed",  # 🆕 Версія API з тегами та фіксами
        "lang": lang
    })