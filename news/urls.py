from django.urls import path
from django.views.generic import TemplateView
from .views import (
    NewsListView, ArticleDetailView, news_digest_view, 
    news_api_view, NewsSitemap, NewsCategorySitemap
)

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
    
    # Sitemap для SEO
    path('sitemap-articles.xml', NewsSitemap.as_view(), name='sitemap_articles'),
    path('sitemap-categories.xml', NewsCategorySitemap.as_view(), name='sitemap_categories'),
    
    # RSS фід (опціонально)
    path('feed/', TemplateView.as_view(template_name='news/rss_feed.xml', content_type='application/rss+xml'), name='rss_feed'),
]