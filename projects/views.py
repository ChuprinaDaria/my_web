from django.shortcuts import render, get_object_or_404
from django.db import models
from .models import Project
from services.models import ServiceCategory
from django.utils.translation import get_language
from django.http import JsonResponse
from django.http import HttpResponse


def projects_list(request):
    lang = get_language()

    categories_with_projects = ServiceCategory.objects.prefetch_related(
        'projects__tags'
    ).annotate(
        projects_count=models.Count('projects', filter=models.Q(projects__is_active=True))
    ).filter(
        projects_count__gt=0
    ).order_by('title_en')

    total_projects = 0
    localized_categories = []

    for category in categories_with_projects:
        projects = category.projects.filter(is_active=True).order_by('-priority', '-order', '-project_date')
        project_count = projects.count()
        total_projects += project_count

        localized_projects = []
        for project in projects:
            localized_projects.append({
                "slug": project.slug,
                "featured_image": project.featured_image,
                "title": getattr(project, f"title_{lang}", project.title_en),
                "short_description": getattr(project, f"short_description_{lang}", project.short_description_en),
                "tags": [
                    {
                        'id': tag.id,
                        'name': tag.get_name(lang),
                        'emoji': getattr(tag, 'icon', '🏷️'),
                        'color': tag.color,
                    }
                    for tag in project.tags.filter(is_active=True)
                ],
                "priority": project.priority,
                "complexity_level": project.complexity_level,
                "project_status": project.project_status,
                "all_badges": project.get_all_badges(lang),
                "technologies_list": project.get_technologies_list(),
                "project_date": project.project_date,
                "development_duration_weeks": project.development_duration_weeks,
            })

        localized_categories.append({
            "id": category.id,
            "slug": category.slug,
            "title": getattr(category, f"title_{lang}", category.title_en),
            "description": getattr(category, f"description_{lang}", category.description_en),
            "short_description": getattr(category, f"description_{lang}", category.description_en)[:200] + "..." if getattr(category, f"description_{lang}", category.description_en) else "",
            "icon": None,  # ServiceCategory не має icon поля
            "projects": localized_projects,
            "projects_count": project_count,
            "featured_image": None,  # ServiceCategory не має featured_image поля
            "service_url": f"/{lang}/services/#{category.slug}",
        })

    featured_projects_qs = Project.objects.filter(
        is_active=True, 
        is_featured=True
    ).select_related('category').prefetch_related('tags').order_by('-priority', '-order', '-project_date')

    related_news = []
    try:
        from news.models import ProcessedArticle
        
        all_project_tags = set()
        for category in categories_with_projects:
            for project in category.projects.filter(is_active=True):
                all_project_tags.update(project.tags.values_list('slug', flat=True))
        
        if all_project_tags:
            related_news = ProcessedArticle.objects.filter(
                status='published',
                tags__slug__in=list(all_project_tags)
            ).distinct().order_by('-published_at')[:10]
            
    except ImportError:
        pass

    try:
        from core.models import Tag
        popular_project_tags = Tag.objects.filter(
            projects__is_active=True,
            is_active=True
        ).annotate(
            projects_usage_count=models.Count('projects', filter=models.Q(projects__is_active=True))
        ).filter(projects_usage_count__gt=0).order_by('-projects_usage_count')[:8]
        
        popular_tags_data = [
            {
                'key': tag.slug,
                'name': tag.get_name(lang),
                'emoji': tag.icon,
                'color': tag.color,
                'usage_count': tag.projects_usage_count,
                'projects_count': tag.projects.filter(is_active=True).count()
            }
            for tag in popular_project_tags
        ]
    except ImportError:
        popular_tags_data = []

    categories_count = categories_with_projects.count()
    
    context = {
        "categories": localized_categories,
        "featured_projects_qs": featured_projects_qs,
        "total_projects": total_projects,
        "total_categories": categories_count,

        "related_news": [
            {
                'uuid': str(article.uuid),
                'title': article.get_title(lang),
                'summary': article.get_summary(lang)[:150] + '...',
                'url': article.get_absolute_url(),
                'image': article.ai_image_url,
                'published_at': article.published_at,
                'category': article.category.get_name(lang) if article.category else '',
            }
            for article in related_news
        ],

        "popular_tags": popular_tags_data,
        "show_tag_filter": bool(popular_tags_data),

        "overview_title": {
            "en": f"{total_projects}+ Projects Across {categories_count} Solutions",
            "uk": f"{total_projects}+ проєктів у {categories_count} рішеннях", 
            "pl": f"{total_projects}+ projektów w {categories_count} rozwiązaniach"
        }.get(lang, ""),
        
        "overview_description": {
            "en": f"Explore our portfolio of {total_projects} completed automation and AI projects. Each solution is cross-connected with relevant insights and services.",
            "uk": f"Досліджуйте наше портфоліо з {total_projects} завершених проєктів автоматизації та ШІ. Кожне рішення пов'язане з відповідними інсайтами та сервісами.",
            "pl": f"Poznaj nasze portfolio {total_projects} ukończonych projektów automatyzacji i AI. Każde rozwiązanie jest połączone z odpowiednimi spostrzeżeniami i usługami."
        }.get(lang, ""),

        "seo_title": {
            "en": f"{total_projects} AI & Automation Projects | Lazysoft Portfolio",
            "uk": f"{total_projects} проєктів ШІ та автоматизації | Портфоліо Lazysoft",
            "pl": f"{total_projects} projektów AI i automatyzacji | Portfolio Lazysoft"
        }.get(lang, ""),
        
        "seo_description": {
            "en": f"Browse {total_projects} completed AI automation projects across {categories_count} service categories. Real client results, technical insights, and cross-connected solutions.",
            "uk": f"Переглядайте {total_projects} завершених проєктів автоматизації ШІ у {categories_count} категоріях сервісів. Реальні результати клієнтів та взаємопов'язані рішення.",
            "pl": f"Przeglądaj {total_projects} ukończonych projektów automatyzacji AI w {categories_count} kategoriach usług. Rzeczywiste wyniki klientów i połączone rozwiązania."
        }.get(lang, ""),
        
        "lang": lang,
    }

    print(f"🎯 Оптимізація: {total_projects} проєктів у {categories_count} категоріях (пусті відфільтровані)")
    print(f"📰 Sidebar: {len(related_news)} новин за тегами")
    print(f"🏷️ Теги: {len(popular_tags_data)} популярних")

    return render(request, "projects/projects.html", context)



from django.shortcuts import get_object_or_404, render
from django.utils.translation import get_language

from django.shortcuts import get_object_or_404, render
from django.utils.translation import get_language

def project_detail(request, slug):
    """
    📋 Детальна сторінка проєкту з крос-промоцією
    Показує пов'язані новини та сервіси через систему тегів (match по Tag.slug).
    У шаблон передаємо вже локалізовані словники.
    """
    project = get_object_or_404(
        Project.objects.prefetch_related('tags', 'review'),
        slug=slug,
        is_active=True
    )
    current_lang = get_language() or 'uk'

    # локалізація з фолбеком: xx → en → базове поле
    def _loc(obj, base):
        return getattr(obj, f"{base}_{current_lang}",
               getattr(obj, f"{base}_en", getattr(obj, base, "")))

    # safe url для файлових полів
    def _url_or_none(f):
        try:
            return f.url if f else None
        except Exception:
            return None

    # --- основні тексти/seo ---
    title = _loc(project, "title")
    seo_title = _loc(project, "seo_title")
    seo_description = _loc(project, "seo_description")

    # --- крос-промо з моделі (якщо є)
    try:
        cross_promotion_content = project.get_cross_promotion_content(limit=6) or []
    except Exception:
        cross_promotion_content = []

    # --- попередні related списки (можуть бути list або QS)
    try:
        raw_related_articles = project.get_related_articles(limit=3) or []
    except Exception:
        raw_related_articles = []
    try:
        raw_related_services = project.get_related_services(limit=3) or []
    except Exception:
        raw_related_services = []

    # --- теги проекту
    project_tags_qs = project.tags.filter(is_active=True)
    tag_slugs = list(project_tags_qs.values_list('slug', flat=True))

    tags_data = [
        {
            'slug': tag.slug,
            'name': getattr(tag, f"name_{current_lang}", getattr(tag, "name_en", tag.name)),
            'icon': getattr(tag, 'icon', None),
            'color': getattr(tag, 'color', None),
            'description': getattr(tag, 'description', ""),
            'usage_count': getattr(tag, 'usage_count', 0),
        }
        for tag in project_tags_qs
    ]

    # --- fallback по тегам (slug), якщо щось із related_* порожнє
    if tag_slugs and ((not raw_related_services) or (not raw_related_articles)):
        try:
            from services.models import Service
        except Exception:
            Service = None
        try:
            from news.models import ProcessedArticle
        except Exception:
            ProcessedArticle = None

        if (not raw_related_services) and Service:
            raw_related_services = (
                Service.objects.filter(is_active=True, tags__slug__in=tag_slugs)
                .distinct().order_by('-priority', '-date_created')[:3]
            )

        if (not raw_related_articles) and ProcessedArticle:
            raw_related_articles = (
                ProcessedArticle.objects.filter(status='published', tags__slug__in=tag_slugs)
                .distinct().order_by('-published_at')[:3]
            )

    # --- нормалізуємо related_* у словники з локалізованими полями
    related_services = []
    for s in raw_related_services:
        related_services.append({
            "slug": getattr(s, "slug", ""),
            "icon": getattr(s, "icon", ""),
            "title": _loc(s, "title"),
            "short_description": _loc(s, "short_description"),
            "featured_image": _url_or_none(getattr(s, "featured_image", None)),
            "priority": getattr(s, "priority", 0),
        })

    related_articles = []
    for a in raw_related_articles:
        try:
            article_url = a.get_absolute_url(current_lang)
        except Exception:
            article_url = f"/{current_lang}/news/article/{getattr(a, 'uuid', '')}/"
        related_articles.append({
            "uuid": str(getattr(a, "uuid", "")),
            "url": article_url,
            "title": a.get_title(current_lang) if hasattr(a, "get_title") else _loc(a, "title"),
            "summary": a.get_summary(current_lang) if hasattr(a, "get_summary") else _loc(a, "summary"),
            "ai_image_url": getattr(a, "ai_image_url", None),
            "published_at": getattr(a, "published_at", None),
        })

    # --- структуровані дані проєкту для шаблону
    project_data = {
        'basic_info': {
            'title': title,
            'short_description': _loc(project, "short_description"),
            'featured_image': _url_or_none(getattr(project, "featured_image", None)),
            'project_url': getattr(project, "project_url", ""),
            'project_date': getattr(project, "project_date", None),
        },
        'content': {
            'client_request': _loc(project, "client_request"),
            'implementation': _loc(project, "implementation"),
            'results': _loc(project, "results"),
            'client_request_extended': getattr(project, f"client_request_extended_{current_lang}", None),
            'implementation_extended': getattr(project, f"implementation_extended_{current_lang}", None),
            'results_extended': getattr(project, f"results_extended_{current_lang}", None),
            'challenges_and_solutions': getattr(project, f"challenges_and_solutions_{current_lang}", None),
            'lessons_learned': getattr(project, f"lessons_learned_{current_lang}", None),
        },
        'metrics': {
            'priority': getattr(project, "priority", 0),
            'complexity_level': getattr(project, "complexity_level", ""),
            'project_status': getattr(project, "project_status", ""),
            'budget_range': getattr(project, "budget_range", ""),
            'development_duration_weeks': getattr(project, "development_duration_weeks", None),
            'client_time_saved_hours': getattr(project, "client_time_saved_hours", None),
        },
        'technical': {
            'technologies_list': project.get_technologies_list() if hasattr(project, "get_technologies_list") else [],
        },
        'media': {
            'gallery_images': [
                _url_or_none(img) for img in [
                    getattr(project, "gallery_image_1", None),
                    getattr(project, "gallery_image_2", None),
                    getattr(project, "gallery_image_3", None),
                ] if img
            ],
            'video_url': getattr(project, "video_url", ""),
            'video_file': _url_or_none(getattr(project, "video_file", None)),
        }
    }

    context = {
        "project": project,
        "project_data": project_data,
        "title": title,
        "seo_title": seo_title,
        "seo_description": seo_description,

        # 🏷️ теги та крос-промо
        "project_tags": tags_data,
        "cross_promotion_content": cross_promotion_content,
        "related_articles": related_articles,   # словники
        "related_services": related_services,   # словники

        # 🎨 оформлення
        "all_badges": project.get_all_badges(current_lang) if hasattr(project, "get_all_badges") else [],
        "priority_level": project.get_priority_level() if hasattr(project, "get_priority_level") else "",
        "complexity_display": project.get_complexity_display_uk() if hasattr(project, "get_complexity_display_uk") else "",
        "status_emoji": project.get_status_emoji() if hasattr(project, "get_status_emoji") else "",

        # UI прапорці
        "show_cross_promotion": bool(cross_promotion_content),
        "show_extended_content": any([
            project_data['content']['client_request_extended'],
            project_data['content']['implementation_extended'],
            project_data['content']['results_extended'],
        ]),

        "lang": current_lang,
    }

    print(
        f"📋 Проєкт '{title}': {project_tags_qs.count()} тег(ів), "
        f"{len(related_articles)} новин, {len(related_services)} сервісів"
    )

    return render(request, "projects/project_detail.html", context)


def projects_api(request):
    """
    🔌 API для проєктів з новою системою тегів
    """
    projects_data = []
    
    for project in Project.objects.filter(is_active=True).prefetch_related('tags'):
        # 🏷️ Додаємо теги до API
        project_tags = [
            {
                'key': tag.slug,
                'name_en': tag.name_en,
                'name_uk': tag.name_uk,
                'name_pl': tag.name_pl,
                'emoji': tag.icon,
                'color': tag.color
            }
            for tag in project.tags.filter(is_active=True)
        ]
        
        projects_data.append({
            "title_en": project.title_en,
            "title_uk": project.title_uk,
            "title_pl": project.title_pl,
            "slug": project.slug,
            "project_date": project.project_date,
            "priority": project.priority,
            "complexity_level": project.complexity_level,
            "project_status": project.project_status,
            
            # 🏷️ НОВІ поля
            "tags": project_tags,
            "related_articles_count": project.get_related_articles().count(),
            "related_services_count": project.get_related_services().count(),
            
            # 🎨 Візуальні бейджі (legacy)
            "is_ai_powered": project.is_ai_powered,
            "is_top_project": project.is_top_project,
            "is_innovative": project.is_innovative,
            "is_enterprise": project.is_enterprise,
            
            # 📊 Метрики
            "budget_range": project.budget_range,
            "technologies_used": project.technologies_used,
        })
    
    return JsonResponse({
        "projects": projects_data,
        "total_count": len(projects_data),
        "api_version": "2.0_with_tags"  # 🆕 Версія API з тегами
    })


def project_contact_submit(request, slug):
    """
    📨 Форма зворотного зв'язку для проєкту
    TODO: Імплементувати відправку форми
    """
    project = get_object_or_404(Project, slug=slug, is_active=True)
    
    if request.method == 'POST':
        # TODO: Обробка POST запиту з формою
        return HttpResponse(f"Contact form submission for '{project.title_en}' is not implemented yet.")
    
    return HttpResponse(f"Contact form for '{project.title_en}' is not implemented yet.")


# 🆕 НОВІ views для фільтрування по тегам
def projects_by_tag(request, tag_key):
    """
    🏷️ Фільтрування проєктів по тегу
    Нова функціональність для крос-навігації
    """
    try:
        from core.models import Tag
        tag = get_object_or_404(Tag, slug=tag_key, is_active=True)
    except ImportError:
        return JsonResponse({'error': 'Tags system not available'}, status=404)
    
    lang = get_language()
    
    # Проєкти з цим тегом
    projects = tag.projects.filter(is_active=True).order_by('-priority', '-project_date')
    
    projects_data = []
    for project in projects:
        projects_data.append({
            "slug": project.slug,
            "title": getattr(project, f"title_{lang}", project.title_en),
            "short_description": getattr(project, f"short_description_{lang}", project.short_description_en),
            "featured_image": project.featured_image.url if project.featured_image else None,
            "priority": project.priority,
            "project_date": project.project_date.isoformat() if project.project_date else None,
        })
    
    # Пов'язаний контент
    related_articles = []
    related_services = []
    
    try:
        from news.models import ProcessedArticle
        related_articles = ProcessedArticle.objects.filter(
            status='published',
            tags__slug=tag_key
        ).distinct().order_by('-published_at')[:3]
    except ImportError:
        pass
    
    try:
        from services.models import ServiceCategory
        related_services = ServiceCategory.objects.filter(
            tags__slug=tag_key
        ).distinct().order_by('-priority')[:3]
    except ImportError:
        pass
    
    context = {
        'tag': {
            'key': tag.slug,
            'name': tag.get_name(lang),
            'emoji': tag.icon,
            'color': tag.color,
            'description': tag.description
        },
        'projects': projects_data,
        'related_articles': [
            {
                'title': article.get_title(lang),
                'url': article.get_absolute_url(),
                'published_at': article.published_at.isoformat() if article.published_at else None
            }
            for article in related_articles
        ],
        'related_services': [
            {
                'title': service.get_title(lang),
                'url': f'/services/{service.slug}/',
            }
            for service in related_services
        ],
        'total_projects': projects.count(),
        'lang': lang
    }
    
    return JsonResponse(context)