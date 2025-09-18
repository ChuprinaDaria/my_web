from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F 
from django.utils.translation import get_language
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView
from django.contrib.sitemaps import Sitemap
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Sum, Count, Avg
from django.template.loader import render_to_string
from .models import ProcessedArticle, NewsCategory, DailyDigest, ROIAnalytics, SocialMediaPost, NewsWidget, RawArticle, AIProcessingLog, Comment
import json
from news.services.ai_processor import AINewsProcessor
from django.views import View
from django.utils.dateparse import parse_date

class NewsListView(ListView):
    """Список новин з SEO оптимізацією"""
    model = ProcessedArticle
    template_name = 'news/news_list.html'
    context_object_name = 'articles'
    paginate_by = 12
    
    def get_queryset(self):
        """Фільтрований список опублікованих статей"""
        language = get_language() or 'uk'
        
        queryset = ProcessedArticle.objects.filter(
            status='published'
        ).select_related('category', 'raw_article__source').order_by('-published_at')
        
        # Фільтр по категорії
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Пошук
        search_query = self.request.GET.get('search')
        if search_query:
            lang_fields = {
                'uk': ['title_uk__icontains', 'summary_uk__icontains'],
                'en': ['title_en__icontains', 'summary_en__icontains'], 
                'pl': ['title_pl__icontains', 'summary_pl__icontains']
            }
            
            fields = lang_fields.get(language, lang_fields['uk'])
            q_objects = Q()
            for field in fields:
                q_objects |= Q(**{field: search_query})
            
            queryset = queryset.filter(q_objects)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Додатковий контекст для шаблону"""
        context = super().get_context_data(**kwargs)
        language = get_language() or 'uk'
        
        # Категорії для навігації
        context['categories'] = NewsCategory.objects.filter(
            is_active=True
        ).annotate(
            articles_count=Count('articles', filter=Q(articles__status='published'))
        ).order_by('order')
        
        # Поточна категорія
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(
                NewsCategory, slug=category_slug
            )
        
        # Пошуковий запит
        context['search_query'] = self.request.GET.get('search', '')
        
        # Інші новини (не топ 10) для sidebar
        top_articles = ProcessedArticle.objects.filter(
            status='published',
            is_top_article=True
        ).order_by('-published_at')[:10]
        
        context['other_news'] = ProcessedArticle.objects.filter(
            status='published'
        ).exclude(
            id__in=[article.id for article in top_articles]
        ).order_by('-published_at')[:8]
        
        # Загальна кількість статей
        context['total_articles'] = ProcessedArticle.objects.filter(
            status='published'
        ).count()
        
        # Пов'язані сервіси для sidebar
        try:
            from services.models import ServiceCategory
            related_services = ServiceCategory.objects.all().order_by('-priority', '-order')[:6]
            
            context['related_services'] = [
                {
                    'slug': s.slug,
                    'title': s.get_title(language),
                    'short': s.get_short(language),
                    'url': f'/{language}/services/{s.slug}/',
                    'icon': s.icon
                }
                for s in related_services
            ]
        except ImportError:
            context['related_services'] = []
        
        # SEO метадані
        if category_slug:
            category = context['current_category']
            context['page_title'] = category.get_name(language)
            context['page_description'] = category.get_description(language)
        else:
            context['page_title'] = 'Tech новини для бізнесу | LAZYSOFT'
            context['page_description'] = 'Останні новини технологій, AI, автоматизації бізнесу. Експертні інсайти для підприємців.'
        
        # Structured data для Google
        context['structured_data'] = self._get_structured_data(context['articles'])
        
        return context
    
    def _get_structured_data(self, articles):
        """Генеруємо JSON-LD для Google"""
        articles_data = []
        for article in articles[:10]:  # Перші 10 статей
            language = get_language() or 'uk'
            articles_data.append({
                "@type": "NewsArticle",
                "headline": article.get_title(language),
                "description": article.get_summary(language),
                "url": self.request.build_absolute_uri(article.get_absolute_url(language)),
                "datePublished": article.published_at.isoformat(),
                "dateModified": article.updated_at.isoformat(),
                "author": {
                    "@type": "Organization",
                    "name": "LAZYSOFT"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "LAZYSOFT",
                    "logo": {
                        "@type": "ImageObject",
                        "url": self.request.build_absolute_uri("/static/images/logo.png")
                    }
                }
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "item": article_data
                }
                for i, article_data in enumerate(articles_data)
            ]
        }

class NewsByDateView(ListView):
    model = ProcessedArticle
    template_name = 'news/news_list.html'  # можна свій шаблон архіву, але можна і цей
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        date_str = self.kwargs['date']  # з URL /news/YYYY-MM-DD/
        target = parse_date(date_str)
        if not target:
            raise Http404("Invalid date")
        return (ProcessedArticle.objects.filter(
                    status='published',
                    published_at__date=target
                )
                .select_related('category', 'raw_article__source')
                .order_by('-published_at'))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        date_str = self.kwargs['date']
        target = parse_date(date_str)
        ctx['archive_date'] = target
        ctx['page_title'] = f"Новини за {target}"
        ctx['page_description'] = f"Всі новини за {target} від Lazysoft."
        ctx['prev_date'] = (target - timedelta(days=1)).isoformat()
        ctx['next_date'] = (target + timedelta(days=1)).isoformat()
        return ctx
    
from django.http import Http404
from django.utils.translation import get_language
from django.views.generic import DetailView
from django.utils import timezone

class ArticleDetailView(DetailView):
    """Детальна сторінка статті з SEO"""
    model = ProcessedArticle
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        article = super().get_object(queryset)
        if article.status != 'published':
            raise Http404("Стаття не опублікована")
        language = get_language() or 'uk'
        article.increment_views(language)
        return article

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = context['article']
        language = get_language() or 'uk'

        # SEO
        context['page_title'] = article.get_meta_title(language) or article.get_title(language)
        context['page_description'] = article.get_meta_description(language) or article.get_summary(language)[:160]
        context['og_title'] = article.get_title(language)
        context['og_description'] = article.get_summary(language)[:200]
        context['og_image'] = article.ai_image_url
        context['og_url'] = self.request.build_absolute_uri()

        # Localized content for template
        context['article_title'] = article.get_title(language)
        context['article_summary'] = article.get_summary(language)
        context['article_business_insight'] = article.get_business_insight(language)
        context['article_business_opportunities'] = article.get_business_opportunities(language)
        context['article_lazysoft_recommendations'] = article.get_lazysoft_recommendations(language)
        context['article_interesting_facts'] = article.get_interesting_facts(language)
        context['category_name'] = article.category.get_name(language)

        # Схожі статті
        context['related_articles'] = ProcessedArticle.objects.filter(
            category=article.category, status='published'
        ).exclude(id=article.id).order_by('-published_at')[:3]

        # Пов'язані сервіси
        context['related_services'] = [
            {
                'slug': s.slug,
                'title': s.get_title(language),
                'short_description': s.get_short_description(language),
                'featured_image': s.featured_image.url if s.featured_image else None
            }
            for s in article.get_related_services(limit=6)
        ]

        # Пов'язані проекти
        context['related_projects'] = [
            {
                'slug': p.slug,
                'title': p.get_title(language),
                'short_description': p.get_short_description(language),
                'featured_image': p.featured_image.url if p.featured_image else None
            }
            for p in article.get_related_projects(limit=6)
        ]

        # Коментарі
        context['comments'] = (
            article.comments
            .filter(is_deleted=False, is_blocked=False, parent__isnull=True)
            .select_related('user')
            .prefetch_related('replies')
        )

        # Structured data
        context['structured_data'] = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": article.get_title(language),
            "description": article.get_summary(language),
            "articleBody": article.get_business_insight(language),
            "url": self.request.build_absolute_uri(),
            "datePublished": article.published_at.isoformat() if article.published_at else article.created_at.isoformat(),
            "dateModified": article.updated_at.isoformat() if article.updated_at else article.created_at.isoformat(),
            "author": {"@type": "Organization", "name": "LAZYSOFT"},
            "publisher": {
                "@type": "Organization",
                "name": "LAZYSOFT",
                "logo": {
                    "@type": "ImageObject",
                    "url": self.request.build_absolute_uri("/static/images/logo.png")
                }
            },
            "mainEntityOfPage": {"@type": "WebPage", "@id": self.request.build_absolute_uri()}
        }

        if article.ai_image_url:
            context['structured_data']['image'] = article.ai_image_url

        # Sidebar data identical to NewsListView
        context['categories'] = NewsCategory.objects.filter(
            is_active=True
        ).annotate(
            articles_count=Count('articles', filter=Q(articles__status='published'))
        ).order_by('order')

        top_articles = ProcessedArticle.objects.filter(
            status='published',
            is_top_article=True
        ).order_by('-published_at')[:10]

        context['other_news'] = ProcessedArticle.objects.filter(
            status='published'
        ).exclude(
            id__in=[a.id for a in top_articles]
        ).exclude(id=article.id).order_by('-published_at')[:8]

        context['total_articles'] = ProcessedArticle.objects.filter(status='published').count()
        context['search_query'] = self.request.GET.get('search', '')

        try:
            from services.models import ServiceCategory
            related_services = ServiceCategory.objects.all().order_by('-priority', '-order')[:6]
            context['related_services'] = [
                {
                    'slug': s.slug,
                    'title': s.get_title(language),
                    'short': s.get_short(language),
                    'url': f'/{language}/services/{s.slug}/',
                    'icon': s.icon
                }
                for s in related_services
            ]
        except Exception:
            context['related_services'] = []

        return context


@cache_page(60 * 15)  # Кешуємо на 15 хвилин
def news_digest_view(request, date=None):
    """Щоденний дайджест новин"""
    if date:
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            raise Http404("Невірний формат дати")
    else:
        target_date = timezone.now().date()
    
    digest = get_object_or_404(DailyDigest, date=target_date, is_published=True)
    language = get_language() or 'uk'
    
    context = {
        'digest': digest,
        'page_title': f"Дайджест новин {digest.date} | LAZYSOFT",
        'page_description': digest.get_summary(language)[:160],
        'structured_data': {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": digest.get_title(language),
            "description": digest.get_summary(language),
            "datePublished": digest.published_at.isoformat() if digest.published_at else digest.created_at.isoformat(),
            "author": {
                "@type": "Organization",
                "name": "LAZYSOFT"
            }
        }
    }
    
    return render(request, 'news/digest_detail.html', context)


def news_api_view(request):
    """API для отримання новин (JSON)"""
    language = request.GET.get('lang', 'uk')
    category = request.GET.get('category')
    limit = min(int(request.GET.get('limit', 10)), 50)
    
    queryset = ProcessedArticle.objects.filter(status='published')
    
    if category:
        queryset = queryset.filter(category__slug=category)
    
    articles = queryset.order_by('-published_at')[:limit]
    
    data = {
        'articles': [
            {
                'id': str(article.uuid),
                'title': article.get_title(language),
                'summary': article.get_summary(language),
                'url': request.build_absolute_uri(article.get_absolute_url(language)),
                'published_at': article.published_at.isoformat(),
                'category': article.category.get_name(language),
                'image': article.ai_image_url,
                'views': article.get_total_views()
            }
            for article in articles
        ],
        'total': articles.count(),
        'language': language
    }
    
    return JsonResponse(data)


# Sitemap для SEO
class NewsSitemap(Sitemap):
    """Sitemap для новин"""
    changefreq = "daily"
    priority = 0.8
    
    def items(self):
        return ProcessedArticle.objects.filter(status='published').order_by('-published_at')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class NewsCategorySitemap(Sitemap):
    """Sitemap для категорій новин"""
    changefreq = "weekly" 
    priority = 0.6
    
    def items(self):
        return NewsCategory.objects.filter(is_active=True)
    
    def location(self, obj):
        return f"/news/category/{obj.slug}/"
    
class ROIDashboardView(View):
    """API для ROI Dashboard - реальний час метрики"""
    
    def get(self, request):
        """Повертає поточні ROI метрики для живого dashboard"""
        today = timezone.now().date()
        
        # Сьогоднішні метрики
        try:
            today_roi = ROIAnalytics.objects.get(date=today)
        except ROIAnalytics.DoesNotExist:
            today_roi = ROIAnalytics.calculate_daily_metrics(today)
        
        # Статистика за місяць
        month_start = today.replace(day=1)
        month_stats = ROIAnalytics.objects.filter(
            date__gte=month_start
        ).aggregate(
            total_savings=Sum('net_savings'),
            total_hours=Sum('manual_hours_saved'),
            total_articles=Sum('articles_processed'),
            total_leads=Sum('new_leads_generated')
        )
        
        # Live статистика системи
        live_stats = {
            'articles_processing': RawArticle.objects.filter(
                is_processed=False, is_duplicate=False
            ).count(),
            'ready_to_publish': ProcessedArticle.objects.filter(
                status='draft'
            ).count(),
            'published_today': ProcessedArticle.objects.filter(
                published_at__date=today
            ).count(),
            'social_posts_scheduled': SocialMediaPost.objects.filter(
                status='scheduled',
                scheduled_at__date=today
            ).count(),
            'ai_cost_today': float(AIProcessingLog.objects.filter(
                created_at__date=today
            ).aggregate(total=Sum('cost'))['total'] or 0)
        }
        
        # Топ категорії за місяць
        top_categories = ProcessedArticle.objects.filter(
            published_at__date__gte=month_start
        ).values('category__name_uk', 'category__icon').annotate(
            count=Count('id'),
            total_views=Sum('views_count_uk') + Sum('views_count_en') + Sum('views_count_pl')
        ).order_by('-count')[:5]
        
        return JsonResponse({
            'success': True,
            'today': {
                'cost_savings': float(today_roi.net_savings),
                'hours_saved': today_roi.manual_hours_saved,
                'articles_processed': today_roi.articles_processed,
                'roi_percentage': today_roi.roi_percentage,
                'new_leads': today_roi.new_leads_generated,
                'time_efficiency': today_roi.time_efficiency
            },
            'month': {
                'total_savings': float(month_stats['total_savings'] or 0),
                'total_hours': month_stats['total_hours'] or 0,
                'total_articles': month_stats['total_articles'] or 0,
                'total_leads': month_stats['total_leads'] or 0,
                'avg_roi': round(today_roi.roi_percentage, 1) if today_roi.roi_percentage else 0
            },
            'live': live_stats,
            'top_categories': list(top_categories),
            'last_updated': timezone.now().isoformat(),
            'chart_data': self._get_chart_data(month_start, today)
        })
    
    def _get_chart_data(self, start_date, end_date):
        """Генерує дані для графіків"""
        daily_data = ROIAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date').values(
            'date', 'net_savings', 'articles_processed', 'manual_hours_saved'
        )
        
        return {
            'savings_trend': [
                {
                    'date': item['date'].isoformat(),
                    'savings': float(item['net_savings']),
                    'articles': item['articles_processed'],
                    'hours': item['manual_hours_saved']
                }
                for item in daily_data
            ]
        }


class NewsWidgetView(View):
    """API для віджетів новин на головній сторінці"""
    
    def get(self, request, widget_id=None):
        """Повертає дані для віджета новин"""
        language = request.GET.get('lang', 'uk')
        format_type = request.GET.get('format', 'json')  # json або html
        
        if widget_id:
            try:
                widget = NewsWidget.objects.get(id=widget_id, is_active=True)
                articles = widget.get_articles(language)
                widget_config = {
                    'name': widget.name,
                    'show_images': widget.show_images,
                    'show_date': widget.show_date,
                    'show_category': widget.show_category,
                    'css_class': widget.css_class,
                    'background_color': widget.background_color,
                    'text_color': widget.text_color
                }
            except NewsWidget.DoesNotExist:
                return JsonResponse({'error': 'Widget not found'}, status=404)
        else:
            # Віджет за замовчанням - топ 5 новин
            articles = ProcessedArticle.objects.filter(
                status='published'
            ).order_by('-priority', '-published_at')[:5]
            
            widget_config = {
                'name': 'Latest Tech News',
                'show_images': True,
                'show_date': True,
                'show_category': True,
                'css_class': 'default-news-widget',
                'background_color': '#ffffff',
                'text_color': '#333333'
            }
        
        # Форматуємо дані статей
        articles_data = []
        for article in articles:
            articles_data.append({
                'id': str(article.uuid),
                'title': article.get_title(language),
                'summary': article.get_summary(language)[:150] + '...',
                'url': article.get_absolute_url(language),
                'category': {
                    'name': article.category.get_name(language),
                    'icon': article.category.icon,
                    'color': article.category.color,
                    'slug': article.category.slug
                },
                'published_at': article.published_at.isoformat(),
                'published_date': article.published_at.strftime('%d.%m.%Y'),
                'published_time': article.published_at.strftime('%H:%M'),
                'reading_time': article.get_reading_time(),
                'image': article.ai_image_url,
                'is_fresh': article.is_fresh(days=3),
                'priority': article.priority,
                'views': article.get_total_views()
            })
        
        # Повертаємо JSON або HTML
        if format_type == 'html':
            html = render_to_string('news/widgets/news_widget.html', {
                'articles': articles_data,
                'widget_config': widget_config,
                'language': language
            })
            return JsonResponse({
                'success': True,
                'html': html,
                'widget_config': widget_config
            })
        else:
            return JsonResponse({
                'success': True,
                'articles': articles_data,
                'widget_config': widget_config,
                'meta': {
                    'total_articles': len(articles_data),
                    'language': language,
                    'generated_at': timezone.now().isoformat()
                }
            })


class SocialMediaStatsView(View):
    """API для статистики соціальних мереж"""
    
    def get(self, request):
        """Повертає статистику постів у соцмережах"""
        days = int(request.GET.get('days', 30))
        start_date = timezone.now().date() - timezone.timedelta(days=days)
        
        # Загальна статистика
        total_stats = SocialMediaPost.objects.filter(
            created_at__date__gte=start_date
        ).aggregate(
            total_posts=Count('id'),
            published_posts=Count('id', filter=Q(status='published')),
            total_likes=Sum('likes_count'),
            total_comments=Sum('comments_count'),
            total_shares=Sum('shares_count'),
            total_reach=Sum('reach_count')
        )
        
        # Статистика по платформах
        platform_stats = SocialMediaPost.objects.filter(
            created_at__date__gte=start_date
        ).values('platform').annotate(
            posts_count=Count('id'),
            published_count=Count('id', filter=Q(status='published')),
            avg_engagement=Avg('likes_count') + Avg('comments_count') + Avg('shares_count'),
            total_reach=Sum('reach_count')
        ).order_by('-posts_count')
        
        # Останні пости
        recent_posts = SocialMediaPost.objects.filter(
            created_at__date__gte=start_date
        ).select_related('article').order_by('-created_at')[:10]
        
        recent_posts_data = []
        for post in recent_posts:
            recent_posts_data.append({
                'id': post.id,
                'platform': post.get_platform_display(),
                'article_title': post.article.title_uk[:50],
                'content': post.content[:100] + '...',
                'status': post.get_status_display(),
                'scheduled_at': post.scheduled_at.isoformat() if post.scheduled_at else None,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'engagement_rate': post.engagement_rate,
                'likes': post.likes_count,
                'comments': post.comments_count,
                'shares': post.shares_count
            })
        
        # Розрахунок середнього engagement rate
        avg_engagement_rate = 0
        if total_stats['total_reach'] and total_stats['total_reach'] > 0:
            total_engagement = (total_stats['total_likes'] or 0) + (total_stats['total_comments'] or 0) + (total_stats['total_shares'] or 0)
            avg_engagement_rate = (total_engagement / total_stats['total_reach']) * 100
        
        return JsonResponse({
            'success': True,
            'period_days': days,
            'total_stats': {
                'total_posts': total_stats['total_posts'],
                'published_posts': total_stats['published_posts'],
                'success_rate': round((total_stats['published_posts'] / total_stats['total_posts'] * 100), 1) if total_stats['total_posts'] > 0 else 0,
                'total_engagement': (total_stats['total_likes'] or 0) + (total_stats['total_comments'] or 0) + (total_stats['total_shares'] or 0),
                'avg_engagement_rate': round(avg_engagement_rate, 2),
                'total_reach': total_stats['total_reach'] or 0
            },
            'platform_breakdown': list(platform_stats),
            'recent_posts': recent_posts_data,
            'generated_at': timezone.now().isoformat()
        })


class NewsAnalyticsAPIView(View):
    """Комплексний API для аналітики новин"""
    
    def get(self, request):
        """Повертає повну аналітику новинної системи"""
        period = request.GET.get('period', '30')  # days
        language = request.GET.get('language', 'all')
        
        days = int(period)
        start_date = timezone.now().date() - timezone.timedelta(days=days)
        
        # Базовий queryset
        articles_qs = ProcessedArticle.objects.filter(
            published_at__date__gte=start_date,
            status='published'
        )
        
        # Фільтр по мові (через перегляди)
        if language != 'all':
            # Тут можна додати більш складну логіку
            pass
        
        # Основна статистика
        main_stats = {
            'total_articles': articles_qs.count(),
            'total_views': articles_qs.aggregate(
                uk=Sum('views_count_uk'),
                en=Sum('views_count_en'), 
                pl=Sum('views_count_pl')
            ),
            'avg_reading_time': articles_qs.aggregate(
                avg_time=Avg('ai_processing_time')
            )['avg_time'] or 0,
            'top_categories': list(articles_qs.values(
                'category__name_uk', 'category__icon', 'category__color'
            ).annotate(
                count=Count('id'),
                total_views=Sum('views_count_uk') + Sum('views_count_en') + Sum('views_count_pl')
            ).order_by('-count')[:5])
        }
        
        # Тренди по дням
        daily_trends = []
        for i in range(days):
            date = start_date + timezone.timedelta(days=i)
            day_articles = articles_qs.filter(published_at__date=date)
            
            daily_trends.append({
                'date': date.isoformat(),
                'articles_count': day_articles.count(),
                'total_views': day_articles.aggregate(
                    total=Sum('views_count_uk') + Sum('views_count_en') + Sum('views_count_pl')
                )['total'] or 0
            })
        
        # Топ статті
        top_articles = articles_qs.annotate(
            total_views=F('views_count_uk') + F('views_count_en') + F('views_count_pl')
        ).order_by('-total_views')[:10]
        
        top_articles_data = []
        for article in top_articles:
            top_articles_data.append({
                'title': article.title_uk,
                'category': article.category.name_uk,
                'views': article.get_total_views(),
                'published_at': article.published_at.isoformat(),
                'url': article.get_absolute_url(),
                'priority': article.get_priority_display()
            })
        
        return JsonResponse({
            'success': True,
            'period': f'{days} days',
            'language_filter': language,
            'main_stats': main_stats,
            'daily_trends': daily_trends,
            'top_articles': top_articles_data,
            'generated_at': timezone.now().isoformat()
        })


# === ФУНКЦІЯ ДЛЯ HOMEPAGE CONTEXT ===
def get_homepage_news_context(language='uk', limit=5):
    """
    Допоміжна функція для отримання новин на головну сторінку
    Використовуй в головному view твого сайту
    """
    
    # Останні важливі новини
    latest_news = ProcessedArticle.objects.filter(
        status='published',
        priority__gte=2  # Середній пріоритет і вище
    ).order_by('-priority', '-published_at')[:limit]
    
    # Форматуємо для шаблону
    news_data = []
    for article in latest_news:
        news_data.append({
            'title': article.get_title(language),
            'summary': article.get_summary(language)[:120] + '...',
            'url': article.get_absolute_url(language),
            'category': {
                'name': article.category.get_name(language),
                'icon': article.category.icon,
                'color': article.category.color
            },
            'published_date': article.published_at.strftime('%d.%m'),
            'reading_time': article.get_reading_time(),
            'is_fresh': article.is_fresh(days=2),
            'priority': article.priority
        })
    
    return {
        'latest_news': news_data,
        'news_widget_config': {
            'show_more_link': '/news/',
            'widget_title': {
                'uk': '🚀 Останні Tech новини',
                'en': '🚀 Latest Tech News', 
                'pl': '🚀 Najnowsze wiadomości Tech'
            }.get(language, '🚀 Останні Tech новини')
        }
    }


# === MIDDLEWARE ДЛЯ ROI TRACKING ===
class ROITrackingMiddleware:
    """Middleware для автоматичного збору ROI метрик"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Трекаємо перегляди новин для ROI
        if request.path.startswith('/news/article/'):
            self._track_article_view(request)
        
        return response
    
    def _track_article_view(self, request):
        """Трекає перегляд статті для ROI розрахунків"""
        try:
            # Можна додати логіку збору метрик
            # Наприклад, збільшити лічильник organic traffic
            pass
        except Exception:
            # Не падаємо якщо tracking не працює
            pass