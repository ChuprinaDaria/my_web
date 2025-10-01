from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap для статичних сторінок сайту"""
    priority = 0.9
    changefreq = 'monthly'
    i18n = True  # Django автоматично згенерує всі мови
    
    def items(self):
        """Список статичних URL - Django автоматично створить версії для всіх мов"""
        return [
            'core:home',           # core/urls.py
            'about:about',         # about/urls.py
            'services:services_list',  # services/urls.py
            'projects:projects',   # projects/urls.py
            'contact_page',        # contacts/urls.py
            'news:news_list',      # news/urls.py
            'consultant:chat',     # consultant/urls.py
        ]
    
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
        return reverse('projects:project_detail', kwargs={'slug': obj.slug})
    
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
        return reverse('news:article_detail', kwargs={'uuid': obj.uuid})
    
    def lastmod(self, obj):
        """Дата останньої модифікації"""
        return obj.published_at or obj.created_at
