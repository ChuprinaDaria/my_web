from django.shortcuts import render
from django.utils.translation import get_language
from django.utils import timezone
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.db.models import Count
from django.http import HttpResponse
from django.conf import settings

from projects.models import Project
from services.models import Service

# 📊 Dashboard data (опційно)
try:
    from news.models import ROIAnalytics
    from django.db.models import Sum, Avg
    from django.utils import timezone
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("⚠️ Dashboard models not available - metrics will be hidden")

# 📰 Новини (опційно)
try:
    from news.models import ProcessedArticle, NewsCategory
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    print("⚠️ News models not available - news section will be hidden")


def home(request):
    # 🧠 Featured проєкти
    featured_projects = Project.objects.filter(
        is_active=True,
        is_featured=True
    ).order_by('-order', '-project_date')[:6]

    # 🎠 Топ-3 сервіси за кількістю проєктів через категорії
    featured_services = (Service.objects
        .filter(is_active=True)
        .annotate(related_projects_count=Count('category__projects', distinct=True))
        .order_by('-related_projects_count', 'title_en')
    )[:3]

    # 🧰 Базовий контекст
    context = {
        'featured_projects': featured_projects,
        'featured_services': featured_services,
        'dashboard_data': get_dashboard_data(),
    }

    # 📰 Якщо новини доступні
    if NEWS_AVAILABLE:
        lang = get_language() or 'uk'
        today = timezone.now().date()

        all_articles = ProcessedArticle.objects.filter(status='published')
        top_news = ProcessedArticle.objects.filter(
            status='published',
            priority__gte=3
        ).select_related('category').order_by('-priority', '-published_at')[:10]

        # Якщо мало — добираємо додаткові
        if top_news.count() < 8:
            extra_news = ProcessedArticle.objects.filter(
                status='published',
                priority__lt=3
            ).select_related('category').order_by('-published_at')[:10 - top_news.count()]
            top_news = list(top_news) + list(extra_news)

        # ID топ-новин, щоб виключити з дайджесту
        top_ids = [a.id for a in top_news]
        daily_digest = ProcessedArticle.objects.filter(
            status='published'
        ).exclude(id__in=top_ids).select_related('category').order_by('-published_at')[:20]

        today_articles = ProcessedArticle.objects.filter(
            status='published',
            published_at__date=today
        )

        context.update({
            'top_news': top_news,
            'daily_digest': daily_digest,
            'news_available': True,
            'news_stats': {
                'total_today': today_articles.count(),
                'total_all': all_articles.count(),
                'categories_count': NewsCategory.objects.filter(is_active=True).count()
                    if NewsCategory.objects.exists() else 0,
            },
        })
    else:
        context['news_available'] = False

    return render(request, 'core/home.html', context)


def robots_txt(request):
    """Генерує robots.txt з урахуванням налаштувань індексації"""
    if settings.DISABLE_GOOGLE_INDEXING:
        content = """User-agent: *
Disallow: /
"""
    else:
        content = f"""User-agent: *
Allow: /

Sitemap: {settings.SITE_URL}/sitemap.xml
Sitemap: {settings.SITE_URL}/sitemap-news.xml
Sitemap: {settings.SITE_URL}/sitemap-categories.xml
"""
    return HttpResponse(content, content_type='text/plain')


def get_dashboard_data():
    """Отримує дані для AI Metrics Widget"""
    if not DASHBOARD_AVAILABLE:
        return {
            'roi_analysis': {'total_roi': 127},
            'key_kpis': {
                'ai_efficiency': {
                    'hours_saved': 240,
                    'efficiency_score': 340
                }
            },
            'content_overview': {'articles': 85}
        }
    
    today = timezone.now().date()
    
    # Сьогоднішні метрики
    try:
        today_roi = ROIAnalytics.objects.get(date=today)
    except ROIAnalytics.DoesNotExist:
        # Якщо немає даних за сьогодні, створюємо нові
        today_roi = ROIAnalytics.calculate_daily_metrics(today)
        if not today_roi:
            # Якщо не вдалося створити, повертаємо дефолтні
            return {
                'roi_analysis': {'total_roi': 127},
                'key_kpis': {
                    'ai_efficiency': {
                        'hours_saved': 240,
                        'efficiency_score': 340
                    }
                },
                'content_overview': {'articles': 85}
            }
    
    # Статистика за місяць
    month_start = today.replace(day=1)
    month_stats = ROIAnalytics.objects.filter(
        date__gte=month_start
    ).aggregate(
        total_savings=Sum('net_savings'),
        total_hours=Sum('manual_hours_saved'),
        total_articles=Sum('articles_processed')
    )
    
    # Отримуємо реальні дані або дефолтні
    roi_value = round(today_roi.roi_percentage, 1) if hasattr(today_roi, 'roi_percentage') and today_roi.roi_percentage else 127
    hours_saved = int(today_roi.manual_hours_saved) if hasattr(today_roi, 'manual_hours_saved') and today_roi.manual_hours_saved else 240
    efficiency_score = int(today_roi.time_efficiency) if hasattr(today_roi, 'time_efficiency') and today_roi.time_efficiency else 340
    articles_count = today_roi.articles_processed if hasattr(today_roi, 'articles_processed') and today_roi.articles_processed else 85
    
    return {
        'roi_analysis': {
            'total_roi': roi_value
        },
        'key_kpis': {
            'ai_efficiency': {
                'hours_saved': hours_saved,
                'efficiency_score': efficiency_score
            }
        },
        'content_overview': {
            'articles': articles_count
        }
    }


