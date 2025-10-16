from django.urls import path
from django.views.generic import TemplateView
from django.http import JsonResponse  
from django.utils import timezone 
from .views import (
    NewsListView, ArticleDetailView, news_digest_view, 
    news_api_view, NewsSitemap, NewsCategorySitemap,
    
    ROIDashboardView, NewsWidgetView, SocialMediaStatsView, NewsAnalyticsAPIView, ProcessedArticle, RawArticle
)
from .views_sitemap import GoogleNewsSitemapView
from .views import NewsByDateView

app_name = 'news'


urlpatterns = [
    # Головна сторінка новин
    path('', NewsListView.as_view(), name='news_list'),
    
    # Новини по категоріях
    path('category/<slug:category_slug>/', NewsListView.as_view(), name='news_category'),
    
    # Детальна сторінка статті
    path('article/<uuid:uuid>/', ArticleDetailView.as_view(), name='article_detail'),
    
    # Щоденні дайджести
    path('digest/', news_digest_view, name='digest_today'),
    path('digest/<str:date>/', news_digest_view, name='digest_detail'),
    
    # API для новин
    path('api/articles/', news_api_view, name='api_articles'),
    
    
    # RSS фід
    path('rss.xml', TemplateView.as_view(template_name='news/rss_feed.xml', content_type='application/rss+xml'), name='rss_feed'),
    
    # Google News Sitemaps - окремі для кожної мови
    path('news-sitemap-uk.xml', GoogleNewsSitemapView('uk'), name='google_news_sitemap_uk'),
    path('news-sitemap-pl.xml', GoogleNewsSitemapView('pl'), name='google_news_sitemap_pl'),
    path('news-sitemap-en.xml', GoogleNewsSitemapView('en'), name='google_news_sitemap_en'),

    # === НОВІ API ENDPOINTS ===
    
    # ROI Dashboard API - для live метрик
    path('api/roi-dashboard/', ROIDashboardView.as_view(), name='roi_dashboard'),
    
    # News Widget API - для головної сторінки
    path('api/news-widget/', NewsWidgetView.as_view(), name='news_widget'),
    path('api/news-widget/<int:widget_id>/', NewsWidgetView.as_view(), name='news_widget_detail'),
    path('<str:date>/', NewsByDateView.as_view(), name='news_by_date'),
    # Social Media Analytics API
    path('api/social-stats/', SocialMediaStatsView.as_view(), name='social_media_stats'),
    
    # Comprehensive News Analytics API
    path('api/analytics/', NewsAnalyticsAPIView.as_view(), name='news_analytics'),
    
    # === JSON ENDPOINTS для AJAX ===
    
    # Швидкий endpoint для живих лічильників
    path('api/live-counters/', 
         lambda request: JsonResponse({
             'articles_pending': RawArticle.objects.filter(is_processed=False).count(),
             'articles_ready': ProcessedArticle.objects.filter(status='draft').count(),
             'articles_published_today': ProcessedArticle.objects.filter(
                 published_at__date=timezone.now().date()
             ).count(),
             'timestamp': timezone.now().isoformat()
         }), 
         name='live_counters'),
]