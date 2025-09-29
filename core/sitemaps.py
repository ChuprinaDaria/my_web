from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings


class StaticViewSitemap(Sitemap):
    """Sitemap для статичних сторінок сайту"""
    priority = 0.9
    changefreq = 'monthly'
    
    def items(self):
        """Список статичних URL для всіх мов"""
        static_urls = []
        languages = ['en', 'uk', 'pl']  # Підтримувані мови
        
        # Основні сторінки для кожної мови
        pages = [
            'core:home',
            'about:about_index', 
            'services:services_index',
            'projects:projects_list',
            'contacts:contacts_index',
            'news:news_list',
        ]
        
        for lang in languages:
            for page in pages:
                try:
                    static_urls.append((page, lang))
                except:
                    pass  # Ігноруємо неіснуючі URL
        
        return static_urls
    
    def location(self, item):
        """Генеруємо URL з мовним префіксом"""
        page, lang = item
        try:
            if lang == 'en':
                return f"/{reverse(page).lstrip('/')}"
            else:
                return f"/{lang}/{reverse(page).lstrip('/')}"
        except:
            return f"/{lang}/"
    
    def lastmod(self, item):
        """Дата останньої модифікації"""
        from django.utils import timezone
        return timezone.now().date()
