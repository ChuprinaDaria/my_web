from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

def home(request):
    """Головна сторінка"""
    from news.models import ProcessedArticle
    from projects.models import Project
    from services.models import ServiceCategory
    
    # Топ-5 новин: спочатку за сьогоднішнім відбором, якщо є; інакше останні топ-статті
    today = timezone.now().date()
    latest_articles = ProcessedArticle.objects.filter(
        status='published',
        is_top_article=True,
        top_selection_date=today,
    ).order_by('article_rank')[:5]
    if latest_articles.count() < 5:
        # Доповнюємо останніми топ-статтями без обов'язкового full_content
        fallback_needed = 5 - latest_articles.count()
        fallback_qs = ProcessedArticle.objects.filter(
            status='published',
            is_top_article=True,
        ).exclude(pk__in=latest_articles.values_list('pk', flat=True)).order_by('-published_at')[:fallback_needed]
        latest_articles = list(latest_articles) + list(fallback_qs)
    
    # Отримуємо дайджест (тепер тільки з ТОП-5 статей)
    from news.models import DailyDigest
    try:
        today_digest = DailyDigest.objects.filter(
            date=timezone.now().date(),
            is_published=True
        ).first()
        
        # Дайджест тепер містить тільки ТОП-5 статей
        if today_digest and latest_articles:
            daily_digest = latest_articles
        else:
            # Якщо немає дайджесту, показуємо ТОП статті за попередні дні
            daily_digest = ProcessedArticle.objects.filter(
                status='published',
                is_top_article=True
            ).order_by('-published_at')[:5]
    except Exception:
        # Fallback: показуємо будь-які опубліковані статті
        daily_digest = ProcessedArticle.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]
    
    # Отримуємо проєкти
    featured_projects = Project.objects.filter(
        is_featured=True
    ).order_by('-date_created')[:4]
    
    # Отримуємо категорії сервісів та адаптуємо під шаблон services_grid.html
    from django.utils.translation import get_language
    language = get_language() or 'uk'
    services = []
    categories = list(ServiceCategory.objects.all().order_by('-priority', '-order')[:6])
    if categories:
        for s in categories:
            title = getattr(s, f'title_{language}', s.title_en)
            short = getattr(s, f'short_description_{language}', '') or ''
            icon_url = s.icon.url if getattr(s, 'icon', None) else None
            main_image_url = s.main_image.url if getattr(s, 'main_image', None) else None
            try:
                priority_emoji = s.get_priority_emoji()
            except Exception:
                priority_emoji = ''
            # теги як прості назви
            try:
                tag_names = [t.get_name(language) for t in s.tags.filter(is_active=True)[:3]] if hasattr(s, 'tags') else []
            except Exception:
                tag_names = []
            services.append({
                'slug': s.slug,
                'title': title,
                'short': short,
                'icon': icon_url,
                'main_image': main_image_url,
                'is_featured': getattr(s, 'is_featured', False),
                'priority_emoji': priority_emoji,
                'projects_count': 0,
                'tags': tag_names,
            })
    else:
        try:
            from services.models import Service
            service_objs = list(Service.objects.filter(is_active=True).order_by('order')[:6])
        except Exception:
            service_objs = []
        for s in service_objs:
            title = getattr(s, f'title_{language}', s.title_en)
            short = getattr(s, f'short_description_{language}', '') or ''
            icon_url = s.icon.url if getattr(s, 'icon', None) else None
            main_image_url = s.category.main_image.url if getattr(getattr(s, 'category', None), 'main_image', None) else None
            try:
                priority_emoji = s.get_priority_emoji()
            except Exception:
                priority_emoji = ''
            try:
                projects_count = s.get_related_projects(limit=3).count() if hasattr(s, 'get_related_projects') else 0
            except Exception:
                projects_count = 0
            try:
                tag_names = [t.get_name(language) for t in s.tags.filter(is_active=True)[:3]] if hasattr(s, 'tags') else []
            except Exception:
                tag_names = []
            services.append({
                'slug': s.slug,
                'title': title,
                'short': short,
                'icon': icon_url,
                'main_image': main_image_url,
                'is_featured': getattr(s, 'is_featured', False),
                'priority_emoji': priority_emoji,
                'projects_count': projects_count,
                'tags': tag_names,
            })
    
    # Hero з адмінки (опціонально)
    try:
        from .models import HomeHero
        hero = HomeHero.objects.filter(is_active=True).order_by('-updated_at').first()
    except Exception:
        hero = None

    # Отримуємо featured product для відображення на головній
    featured_product = None
    featured_products = []
    try:
        from products.models import Product
        featured_product = Product.objects.filter(
            is_active=True,
            is_featured=True
        ).order_by('-priority', '-date_created').first()
        
        # Отримуємо всі featured products для секції
        featured_products_qs = Product.objects.filter(
            is_active=True,
            is_featured=True
        ).order_by('-priority', 'order')[:3]  # Топ-3 продукти
        
        # Підготовка даних для шаблону
        for product in featured_products_qs:
            featured_products.append({
                'url': product.get_absolute_url(language),
                'title': product.get_title(language),
                'short_description': product.get_short_description(language) or '',
                'image': product.featured_image,
                'icon': product.icon,
                'cta_text': product.get_cta_text(language),
                'is_featured': product.is_featured,
                'is_top': product.priority >= 5,
                'priority': product.priority,
                'packages_count': product.pricing_packages.filter(is_active=True).count(),
                'tags': list(product.tags.filter(is_active=True)[:3]) if hasattr(product, 'tags') else [],
            })
    except Exception:
        pass

    # Отримуємо AboutCard для відображення на головній
    about_card = None
    try:
        from .models import AboutCard
        about_card = AboutCard.objects.filter(is_active=True).order_by('order', '-updated_at').first()
    except Exception:
        pass

    # Нормалізуємо до списку для шаблону та прапорця наявності
    latest_articles_list = list(latest_articles)

    context = {
        'latest_articles': latest_articles_list,
        'top_news': latest_articles_list,  # Для сумісності з шаблоном
        'news_available': bool(latest_articles_list),  # Перевірка наявності новин
        'daily_digest': daily_digest,  # Дайджест новин
        'featured_projects': featured_projects,
        'services': services,
        'home_hero': hero,
        'featured_product': featured_product,  # Додано для ProductCard (один)
        'featured_products': featured_products,  # Додано для Products Home Section (список)
        'about_card': about_card,  # Додано для AboutCard
    }

    return render(request, 'core/home.html', context)

class WidgetMetricsAPIView(TemplateView):
    """API для метрик віджетів"""
    
    def get(self, request, *args, **kwargs):
        period = request.GET.get('period', 'month')
        
        # Тут можна додати логіку для отримання метрик
        data = {
            'period': period,
            'metrics': {
                'articles_count': 0,
                'projects_count': 0,
                'services_count': 0,
            }
        }
        
        return JsonResponse(data)

class PublicDashboardAPIView(TemplateView):
    """Публічні метрики для AI widgets (без чутливих даних)."""

    def get(self, request, *args, **kwargs):
        period = request.GET.get('period', 'month')
        try:
            from lazysoft.dashboard import LazySOFTDashboardAdmin
            dashboard_admin = LazySOFTDashboardAdmin()
            full = dashboard_admin.get_executive_summary(period)

            # Витягуємо та мапимо AI метрики під віджет
            ai_metrics = full.get('ai_metrics', {}) or {}
            by_model = ai_metrics.get('by_model', {}) or {}
            # Обираємо топ-модель за сумарною вартістю або кількістю викликів
            ai_top_model = ''
            if by_model:
                ai_top_model = max(
                    by_model.items(), key=lambda kv: (kv[1].get('total_cost', 0), kv[1].get('calls', 0))
                )[0]

            safe_data = {
                'roi_analysis': full.get('roi_analysis', {}),
                'content_overview': full.get('content_overview', {}),
                'key_kpis': full.get('key_kpis', {}),
                'ai_spend_usd': float(ai_metrics.get('total_cost', 0.0) or 0.0),
                'ai_spend_by_model': by_model,
                'ai_top_model': ai_top_model,
            }

            return JsonResponse({
                'period': period,
                'data': safe_data,
                'last_updated': timezone.now().strftime('%H:%M')
            })
        except Exception as e:
            logger.error(f"PublicDashboardAPIView error: {e}")
            return JsonResponse({'period': period, 'data': {}, 'error': 'unavailable'}, status=500)

def robots_txt(request):
    """Robots.txt для SEO"""
    from django.http import HttpResponse
    from django.conf import settings
    
    site_url = getattr(settings, 'SITE_URL', 'https://lazysoft.pl')
    
    content = f"""# Google News Bot - special rules for news indexing
User-agent: Googlebot-News
Allow: /news/
Allow: /uk/news/
Allow: /pl/news/
Allow: /en/news/

# Google Image Bot - allow images for Rich Results
User-agent: Googlebot-Image
Allow: /media/projects/
Allow: /media/services/
Allow: /media/products/
Allow: /static/images/

# General crawlers
User-agent: *
Allow: /
Allow: /media/projects/
Allow: /media/services/
Allow: /media/products/
Allow: /static/images/

# Sitemaps
Sitemap: {site_url}/sitemap.xml
Sitemap: {site_url}/news-sitemap-uk.xml
Sitemap: {site_url}/news-sitemap-pl.xml
Sitemap: {site_url}/news-sitemap-en.xml
Sitemap: {site_url}/sitemap-static.xml
Sitemap: {site_url}/sitemap-services.xml
Sitemap: {site_url}/sitemap-projects.xml
Sitemap: {site_url}/sitemap-articles.xml
Sitemap: {site_url}/sitemap-news.xml
Sitemap: {site_url}/sitemap-categories.xml

# Disallow admin and control panels
Disallow: /admin/
Disallow: /control/
Disallow: /account/
Disallow: /api/

# Allow important pages and media
Allow: /en/
Allow: /uk/
Allow: /pl/
Allow: /services/
Allow: /projects/
Allow: /products/
Allow: /news/
Allow: /about/
Allow: /contacts/
Allow: /consultant/

# Disallow only sensitive files
Disallow: /static/admin/
Disallow: /static/ckeditor/
Disallow: /media/company/
Disallow: /media/contacts/

# Crawl delay
Crawl-delay: 1
"""
    
    return HttpResponse(content, content_type='text/plain')

def error_400(request, exception=None):
    return render(request, 'core/errors/400.html', status=400)

def error_401(request, exception=None):
    return render(request, 'core/errors/401.html', status=401)

def error_403(request, exception=None):
    return render(request, 'core/errors/403.html', status=403)

def error_404(request, exception=None):
    return render(request, 'core/errors/404.html', status=404)

def error_500(request):
    return render(request, 'core/errors/500.html', status=500)

def csrf_failure(request, reason=''):
    return render(request, 'core/errors/403.html', {'message': 'CSRF verification failed. Request aborted.'}, status=403)