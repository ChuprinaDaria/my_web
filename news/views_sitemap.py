from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from datetime import timedelta
from .models import ProcessedArticle


class GoogleNewsSitemapView:
    """Кастомний view для Google News sitemap з правильними тегами"""
    
    def __init__(self):
        self.sitemap = GoogleNewsSitemap()
    
    def __call__(self, request):
        """Обробляє запит до Google News sitemap"""
        try:
            # Отримуємо статті за останні 2 дні
            two_days_ago = timezone.now() - timedelta(days=2)
            articles = ProcessedArticle.objects.filter(
                status='published',
                published_at__gte=two_days_ago
            ).order_by('-published_at')
            
            # Підготовляємо дані для template
            urlset = []
            for article in articles:
                # Отримуємо URL статті
                if hasattr(article, 'get_absolute_url'):
                    location = article.get_absolute_url(language='uk')
                else:
                    from django.urls import reverse
                    location = reverse('news:article_detail', kwargs={'uuid': article.uuid})
                
                # Підготовляємо метадані для Google News
                urlset.append({
                    'location': request.build_absolute_uri(location),
                    'lastmod': article.published_at or article.updated_at,
                    'changefreq': 'hourly',
                    'priority': 0.8,
                    'news_title': article.get_title('uk'),
                    'news_keywords': self._get_keywords(article),
                })
            
            # Рендеримо template
            content = render_to_string('news/google_news_sitemap.xml', {
                'urlset': urlset
            })
            
            return HttpResponse(content, content_type='application/xml')
            
        except Exception as e:
            print(f"Google News Sitemap error: {e}")
            # Повертаємо порожній sitemap у разі помилки
            empty_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
</urlset>'''
            return HttpResponse(empty_content, content_type='application/xml')
    
    def _get_keywords(self, article):
        """Отримує ключові слова для статті"""
        keywords = []
        
        # Додаємо категорію
        if article.category:
            keywords.append(article.category.get_name('uk'))
        
        # Додаємо теги
        if hasattr(article, 'tags') and article.tags.exists():
            keywords.extend([tag.get_name('uk') for tag in article.tags.all()])
        
        # Додаємо ключові слова з RSS категорії
        if hasattr(article, 'raw_article') and article.raw_article.source:
            rss_category = article.raw_article.source.get_category_display()
            if rss_category:
                keywords.append(rss_category)
        
        return ', '.join(keywords[:10])  # Максимум 10 ключових слів


class GoogleNewsSitemap(Sitemap):
    """Sitemap клас для Google News (використовується в view)"""
    priority = 0.8
    changefreq = 'hourly'
    
    def items(self):
        """Повертає QuerySet новин за останні 2 дні"""
        try:
            two_days_ago = timezone.now() - timedelta(days=2)
            return ProcessedArticle.objects.filter(
                status='published',
                published_at__gte=two_days_ago
            ).order_by('-published_at')
        except Exception:
            return []
    
    def lastmod(self, obj):
        return obj.published_at or obj.updated_at
    
    def location(self, obj):
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url(language='uk')
        else:
            from django.urls import reverse
            return reverse('news:article_detail', kwargs={'uuid': obj.uuid})
