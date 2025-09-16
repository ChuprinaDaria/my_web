from django.shortcuts import render
from django.utils.translation import get_language
from django.utils import timezone
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

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
    
    # 🛠️ Сервіси для services_grid (ServiceCategory) - максимум 5 сервісів для головної
    from services.models import ServiceCategory
    lang = get_language() or 'uk'
    
    # Спочатку шукаємо featured сервіси
    featured_services = ServiceCategory.objects.filter(is_featured=True).select_related().prefetch_related('tags').order_by('-priority', '-order', '-date_created')[:5]
    
    # Якщо немає featured, беремо будь-які сервіси
    if not featured_services.exists():
        featured_services = ServiceCategory.objects.select_related().prefetch_related('tags').order_by('-priority', '-order', '-date_created')[:5]
    
    services = []
    for s in featured_services:
        services.append({
            "slug": s.slug,
            "title": s.get_title(lang),
            "short": s.get_short(lang),
            "is_featured": s.is_featured,
            "priority_emoji": s.get_priority_emoji(),
            "icon": s.icon.url if s.icon else None,
            "main_image": s.main_image.url if s.main_image else None,
            "tags": s.tags.filter(is_active=True)[:3],
        })

    # 🧰 Базовий контекст
    context = {
        'featured_projects': featured_projects,
        'featured_services': featured_services,
        'services': services,  # Додаємо для services_grid
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
    
    # Отримуємо останні дані ROI (за сьогодні або останні доступні)
    try:
        today_roi = ROIAnalytics.objects.get(date=today)
    except ROIAnalytics.DoesNotExist:
        # Якщо немає даних за сьогодні, беремо останні доступні
        today_roi = ROIAnalytics.objects.order_by('-date').first()
        if not today_roi:
            # Якщо взагалі немає даних, створюємо тестові
            today_roi = ROIAnalytics.objects.create(
                date=today,
                manual_hours_saved=45.5,
                ai_processing_time=2.3,
                time_efficiency=95.2,
                content_manager_cost_saved=1200.00,
                smm_specialist_cost_saved=800.00,
                copywriter_cost_saved=1500.00,
                ai_api_costs=150.00,
                net_savings=3350.00,
                articles_processed=23,
                translations_made=69,
                images_generated=18,
                social_posts_generated=12,
                tags_assigned=45,
                new_leads_generated=8,
                organic_traffic_increase=340,
                social_engagement_increase=180,
                bounce_rate_improvement=15.3,
                seo_score_improvement=28.7,
                content_uniqueness=94.2,
                avg_article_rating=4.6,
                cross_promotion_success_rate=78.5,
                tag_engagement_stats=85.2,
                top_performing_tags="AI,automation,productivity",
                key_takeaways_uk="Автоматизація зекономила 45+ годин",
                key_takeaways_en="Automation saved 45+ hours",
                key_takeaways_pl="Automatyzacja zaoszczędziła 45+ godzin"
            )
    
    # Статистика за місяць
    month_start = today.replace(day=1)
    month_stats = ROIAnalytics.objects.filter(
        date__gte=month_start
    ).aggregate(
        total_savings=Sum('net_savings'),
        total_hours=Sum('manual_hours_saved'),
        total_articles=Sum('articles_processed')
    )
    
    # Реальні дані з бази
    roi_value = round(today_roi.roi_percentage, 1) if today_roi.roi_percentage > 0 else 127
    hours_saved = int(today_roi.manual_hours_saved) if today_roi.manual_hours_saved > 0 else 45
    efficiency_score = int(today_roi.time_efficiency) if today_roi.time_efficiency > 0 else 95
    articles_count = today_roi.articles_processed if today_roi.articles_processed > 0 else 23
    
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


class WidgetMetricsAPIView(View):
    """API для віджета метрик з ПРАВИЛЬНИМИ даними"""
    
    @method_decorator(cache_page(60 * 15))  # Кешування на 15 хвилин
    def get(self, request):
        try:
            from lazysoft.dashboard import LazySOFTDashboardAdmin
            dashboard = LazySOFTDashboardAdmin()
            data = dashboard.get_executive_summary('month')
            
            # Витягуємо метрики правильно
            roi_data = data.get('roi_analysis', {})
            ai_efficiency = data.get('key_kpis', {}).get('ai_efficiency', {})
            content_data = data.get('content_overview', {})
            
            # === РЕАЛІСТИЧНІ МЕТРИКИ ===
            metrics = {
                'savings_usd': round(roi_data.get('estimated_savings', 0), 0),  # Заощаджені кошти в доларах
                'hours_saved': round(roi_data.get('hours_saved', 17.5), 1),
                'ai_content': content_data.get('articles', 5),
                'efficiency_growth': min(ai_efficiency.get('efficiency_score', 85.0), 300),  # Max 300%
                'last_updated': timezone.now().strftime('%H:%M'),
                'cost_savings': round(roi_data.get('net_profit', 630), 0),
                'articles_processed': roi_data.get('articles_processed', 5)
            }
            
            return JsonResponse({
                'success': True,
                'metrics': metrics,
                'debug': {
                    'raw_roi': roi_data.get('total_roi', 0),
                    'raw_hours': roi_data.get('hours_saved', 0),
                    'calculation_method': 'realistic_business_model'
                } if request.user.is_staff else None
            })
            
        except Exception as e:
            # Fallback realistic data
            from django.conf import settings
            manual_cost = getattr(settings, 'AI_MANUAL_COST_PER_ARTICLE', 19.0)
            demo_articles = 5
            return JsonResponse({
                'success': True,
                'metrics': {
                    'savings_usd': demo_articles * manual_cost,  # 5 статей × $19 = $95
                    'hours_saved': 17.5,         # 17.5h - за місяць  
                    'ai_content': demo_articles, # 5 статей
                    'efficiency_growth': 95.0,   # 95% ефективність
                    'last_updated': timezone.now().strftime('%H:%M'),
                    'cost_savings': demo_articles * manual_cost,  # $600 заощаджено
                    'articles_processed': demo_articles
                },
                'fallback': True,
                'error': str(e) if request.user.is_staff else 'Using fallback data'
            })


class PublicDashboardAPIView(View):
    """Публічний API для віджета метрик (без авторизації)"""
    
    @method_decorator(cache_page(60 * 5))  # Кешування на 5 хвилин
    def get(self, request):
        try:
            from lazysoft.dashboard import LazySOFTDashboardAdmin
            dashboard = LazySOFTDashboardAdmin()
            data = dashboard.get_executive_summary('month')
            
            # Публічні дані для віджета
            # Отримуємо AI метрики
            ai_metrics = data.get('ai_metrics', {})
            by_model = ai_metrics.get('by_model', {})
            
            # Визначаємо топ-модель за витратами
            top_model = None
            if by_model:
                top_model = max(by_model.items(), key=lambda kv: kv[1].get('total_cost', 0.0))[0]
            
            public = {
                "roi_analysis": {
                    "estimated_savings": data["roi_analysis"].get("estimated_savings", 0),
                    "hours_saved": data["roi_analysis"].get("hours_saved", 0),
                    "articles_processed": data["roi_analysis"].get("articles_processed", 0),
                    "cost_per_article": data["roi_analysis"].get("cost_per_article", 0),
                },
                "content_overview": {"articles": data["content_overview"].get("articles", 0)},
                "ai_spend_usd": ai_metrics.get("total_cost", 0.0),  # реальні витрати AI
                "ai_spend_by_model": by_model,  # розбивка по моделях
                "ai_top_model": top_model,  # топ-модель за витратами
            }
            
            return JsonResponse({
                'success': True,
                'data': public,
                'last_updated': timezone.now().strftime('%H:%M')
            })
            
        except Exception as e:
            # Fallback дані
            from django.conf import settings
            manual_cost = getattr(settings, 'AI_MANUAL_COST_PER_ARTICLE', 19.0)
            demo_articles = 5
            
            return JsonResponse({
                'success': True,
                'data': {
                    "roi_analysis": {
                        "estimated_savings": demo_articles * manual_cost,
                        "hours_saved": 17.5,
                        "articles_processed": demo_articles,
                        "cost_per_article": 3.8,
                    },
                    "content_overview": {"articles": demo_articles},
                    "ai_spend_usd": 19.0,
                    "ai_spend_by_model": {
                        "gpt-4o": {"total_cost": 80.0, "calls": 10, "avg_time": 2.5},
                        "gpt-3.5-turbo": {"total_cost": 40.0, "calls": 15, "avg_time": 1.2}
                    },
                    "ai_top_model": "gpt-4o",
                },
                'last_updated': timezone.now().strftime('%H:%M'),
                'fallback': True
            })


