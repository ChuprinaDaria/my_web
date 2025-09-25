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
    
    # Отримуємо останні новини
    latest_articles = ProcessedArticle.objects.filter(
        status='published'
    ).order_by('-published_at')[:3]
    
    # Отримуємо дайджест (додаткові новини після топ-3)
    daily_digest = ProcessedArticle.objects.filter(
        status='published'
    ).order_by('-published_at')[3:13]  # Наступні 10 статей після топ-3
    
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

    context = {
        'latest_articles': latest_articles,
        'top_news': latest_articles,  # Для сумісності з шаблоном
        'news_available': latest_articles.exists(),  # Перевірка наявності новин
        'daily_digest': daily_digest,  # Дайджест новин
        'featured_projects': featured_projects,
        'services': services,
        'home_hero': hero,
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
    
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /account/
Disallow: /api/
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