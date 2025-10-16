from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from datetime import timedelta
from .models import ProcessedArticle


class GoogleNewsSitemap(Sitemap):
    """Google News Sitemap з правильними тегами для Google News"""
    priority = 0.8
    changefreq = 'hourly'  # Google News перевіряє частіше
    i18n = True
    
    def items(self):
        """Повертає QuerySet новин за останні 2 дні"""
        try:
            two_days_ago = timezone.now() - timedelta(days=2)
            return ProcessedArticle.objects.filter(
                status='published',
                published_at__gte=two_days_ago
            ).order_by('-published_at')
        except Exception as e:
            print(f"GoogleNewsSitemap: не вдалося завантажити статті: {e}")
            return []
    
    def lastmod(self, obj):
        """Повертає дату публікації"""
        return obj.published_at or obj.updated_at
    
    def location(self, obj):
        """URL детальної сторінки статті"""
        # Використовуємо метод get_absolute_url з явною мовою
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url(language='uk')  # Українська як основна
        else:
            return reverse('news:article_detail', kwargs={'uuid': obj.uuid})
    
    def get_urls(self, page=1, site=None, protocol=None):
        """Перевизначаємо для додавання Google News тегів"""
        urls = super().get_urls(page, site, protocol)
        
        # Додаємо Google News namespace
        for url in urls:
            if hasattr(url, 'location'):
                if not hasattr(url, 'namespaces'):
                    url.namespaces = {}
                url.namespaces['news'] = 'http://www.google.com/schemas/sitemap-news/0.9'
        
        return urls


class NewsSitemap(Sitemap):
    """Звичайний sitemap для новин (для загальної індексації)"""
    priority = 0.7
    changefreq = 'daily'
    i18n = True
    
    def items(self):
        """Повертає QuerySet всіх опублікованих новин"""
        try:
            return ProcessedArticle.objects.filter(status='published').order_by('-published_at')
        except Exception as e:
            print(f"NewsSitemap: не вдалося завантажити статті: {e}")
            return []
    
    def lastmod(self, obj):
        """Повертає дату останньої модифікації"""
        return obj.updated_at or obj.published_at
    
    def location(self, obj):
        """URL детальної сторінки статті"""
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url(language='uk')
        else:
            return reverse('news:article_detail', kwargs={'uuid': obj.uuid})
