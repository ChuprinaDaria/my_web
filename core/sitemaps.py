from django.contrib.sitemaps import Sitemap
from django.urls import reverse, NoReverseMatch
import logging

logger = logging.getLogger(__name__)


class StaticViewSitemap(Sitemap):
    """Sitemap для статичних сторінок сайту"""
    priority = 0.9
    changefreq = 'monthly'
    i18n = True  # Django автоматично згенерує всі мови
    
    def items(self):
        """Список статичних URL з перевіркою, щоб уникнути 500 у разі NoReverseMatch"""
        candidates = [
            'core:home',                 # core/urls.py (namespaced)
            'about:about',               # about/urls.py (namespaced)
            'services:services_list',    # services/urls.py (namespaced)
            'projects',                  # projects/urls.py (без namespace у include)
            'contacts:contact_page',     # contacts/urls.py (namespaced)
            'news:news_list',            # news/urls.py (namespaced)
            'consultant:chat',           # consultant/urls.py (namespaced)
        ]

        valid = []
        for name in candidates:
            try:
                # Перевіряємо, що reverse працює; i18n префікс додасться під час побудови
                reverse(name)
                valid.append(name)
            except NoReverseMatch:
                logger.warning("Sitemap: пропускаємо невалідне ім'я маршруту: %s", name)
                continue
        return valid
    
    def location(self, item):
        """Генеруємо URL - Django автоматично додасть мовний префікс"""
        return reverse(item)


class ServiceDetailSitemap(Sitemap):
    """Sitemap для детальних сторінок послуг"""
    priority = 0.8
    changefreq = 'weekly'
    i18n = True
    
    def items(self):
        """Отримуємо всі активні послуги"""
        try:
            from services.models import ServiceCategory
            return ServiceCategory.objects.all()
        except ImportError:
            return []
    
    def location(self, obj):
        """URL детальної сторінки послуги"""
        return reverse('services:service_detail', kwargs={'slug': obj.slug})
    
    def lastmod(self, obj):
        """Дата останньої модифікації"""
        return obj.date_created


class ProjectDetailSitemap(Sitemap):
    """Sitemap для детальних сторінок проєктів"""
    priority = 0.8
    changefreq = 'weekly'
    i18n = True
    
    def items(self):
        """Отримуємо всі активні проєкти"""
        try:
            from projects.models import Project
            return Project.objects.filter(is_active=True)
        except ImportError:
            return []
    
    def location(self, obj):
        """URL детальної сторінки проєкту"""
        return reverse('project_detail', kwargs={'slug': obj.slug})
    
    def lastmod(self, obj):
        """Дата останньої модифікації"""
        return obj.date_created


class ArticleDetailSitemap(Sitemap):
    """Sitemap для детальних сторінок статей"""
    priority = 0.7
    changefreq = 'daily'
    i18n = True
    
    def items(self):
        """Отримуємо всі опубліковані статті"""
        try:
            from news.models import ProcessedArticle
            return ProcessedArticle.objects.filter(status='published')
        except ImportError:
            return []
    
    def location(self, obj):
        """URL детальної сторінки статті"""
        # Використовуємо метод get_absolute_url з явною мовою для уникнення i18n проблем
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url(language='pl')  # Дефолтна мова
        else:
            return reverse('news:article_detail', kwargs={'uuid': obj.uuid})
    
    def lastmod(self, obj):
        """Дата останньої модифікації"""
        return obj.published_at or obj.created_at


class NewsSitemap(Sitemap):
    """Sitemap для новин з підтримкою Google News"""
    priority = 0.7
    changefreq = 'daily'
    i18n = True
    
    def items(self):
        """Повертає QuerySet новин за останні 2 дні"""
        try:
            from news.models import ProcessedArticle
            from django.utils import timezone
            from datetime import timedelta
            
            two_days_ago = timezone.now() - timedelta(days=2)
            return ProcessedArticle.objects.filter(
                status='published',
                published_at__gte=two_days_ago
            ).order_by('-published_at')
        except (ImportError, Exception) as e:
            # Якщо база даних недоступна або інша помилка, повертаємо порожній список
            print(f"NewsSitemap: не вдалося завантажити статті: {e}")
            return []
    
    def lastmod(self, obj):
        """Повертає updated_at або published_at кожної статті"""
        return obj.updated_at or obj.published_at
    
    def location(self, obj):
        """URL детальної сторінки статті"""
        # Використовуємо метод get_absolute_url з явною мовою для уникнення i18n проблем
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url(language='pl')  # Дефолтна мова
        else:
            return reverse('news:article_detail', kwargs={'uuid': obj.uuid})
    
    def get_urls(self, page=1, site=None, protocol=None):
        """Перевизначаємо для додавання namespace Google News"""
        urls = super().get_urls(page, site, protocol)
        
        # Додаємо namespace для Google News
        for url in urls:
            if hasattr(url, 'location'):
                # Додаємо xmlns:news namespace до URL
                if not hasattr(url, 'namespaces'):
                    url.namespaces = {}
                url.namespaces['news'] = 'http://www.google.com/schemas/sitemap-news/0.9'
        
        return urls


class NewsCategorySitemap(Sitemap):
    """Sitemap для категорій новин"""
    priority = 0.6
    changefreq = 'weekly'
    i18n = True
    
    def items(self):
        try:
            from news.models import NewsCategory
            return NewsCategory.objects.filter(is_active=True)
        except ImportError:
            return []
    
    def location(self, obj):
        return reverse('news:news_category', kwargs={'category_slug': obj.slug})
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else None
