from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from datetime import timedelta
from .models import ProcessedArticle


class NewsUkrainianSitemap(Sitemap):
    """Sitemap для українських новин за останні 2 дні"""
    # Прибираємо changefreq та priority для Google News
    i18n = False  # Окремий sitemap для однієї мови

    def items(self):
        """Тільки українські новини за останні 2 дні"""
        try:
            two_days_ago = timezone.now() - timedelta(days=2)
            return ProcessedArticle.objects.filter(
                status='published',
                published_at__gte=two_days_ago
            ).order_by('-published_at')
        except Exception as e:
            print(f"NewsUkrainianSitemap: не вдалося завантажити статті: {e}")
            return []

    def lastmod(self, obj):
        """Повертає datetime останньої модифікації в UTC для Django Sitemap.

        ВАЖЛИВО: Django очікує об'єкт date/datetime, а не рядок.
        Форматування у W3C-формат робить сам sitemap, тому не використовуємо strftime().
        """
        lastmod = obj.published_at or obj.updated_at
        if lastmod:
            # Повертаємо aware datetime в UTC
            return lastmod.astimezone(timezone.utc)
        # fallback: поточний час в UTC
        return timezone.now().astimezone(timezone.utc)

    def location(self, obj):
        """URL детальної сторінки статті українською"""
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url(language='uk')
        else:
            return reverse('news:article_detail', kwargs={'uuid': obj.uuid})


class NewsPolishSitemap(Sitemap):
    """Sitemap для польських новин за останні 2 дні"""
    i18n = False

    def items(self):
        """Тільки польські новини за останні 2 дні"""
        try:
            two_days_ago = timezone.now() - timedelta(days=2)
            return ProcessedArticle.objects.filter(
                status='published',
                published_at__gte=two_days_ago
            ).order_by('-published_at')
        except Exception as e:
            print(f"NewsPolishSitemap: не вдалося завантажити статті: {e}")
            return []

    def lastmod(self, obj):
        """Повертає datetime останньої модифікації в UTC"""
        lastmod = obj.published_at or obj.updated_at
        if lastmod:
            return lastmod.astimezone(timezone.utc)
        return timezone.now().astimezone(timezone.utc)

    def location(self, obj):
        """URL детальної сторінки статті польською"""
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url(language='pl')
        else:
            return reverse('news:article_detail', kwargs={'uuid': obj.uuid})


class NewsEnglishSitemap(Sitemap):
    """Sitemap для англійських новин за останні 2 дні"""
    i18n = False

    def items(self):
        """Тільки англійські новини за останні 2 дні"""
        try:
            two_days_ago = timezone.now() - timedelta(days=2)
            return ProcessedArticle.objects.filter(
                status='published',
                published_at__gte=two_days_ago
            ).order_by('-published_at')
        except Exception as e:
            print(f"NewsEnglishSitemap: не вдалося завантажити статті: {e}")
            return []

    def lastmod(self, obj):
        """Повертає datetime останньої модифікації в UTC"""
        lastmod = obj.published_at or obj.updated_at
        if lastmod:
            return lastmod.astimezone(timezone.utc)
        return timezone.now().astimezone(timezone.utc)

    def location(self, obj):
        """URL детальної сторінки статті англійською"""
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url(language='en')
        else:
            return reverse('news:article_detail', kwargs={'uuid': obj.uuid})


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
