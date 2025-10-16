from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from datetime import timedelta
from .models import ProcessedArticle


class GoogleNewsSitemapView:
    """Кастомний view для Google News sitemap з правильними тегами"""
    
    def __init__(self, language='uk'):
        self.language = language
        self.sitemap = GoogleNewsSitemap()
    
    def __call__(self, request):
        """Обробляє запит до Google News sitemap для конкретної мови"""
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
                # Отримуємо URL статті для конкретної мови
                if hasattr(article, 'get_absolute_url'):
                    location = article.get_absolute_url(language=self.language)
                else:
                    from django.urls import reverse
                    location = reverse('news:article_detail', kwargs={'uuid': article.uuid})
                
                # Конвертуємо дату в UTC
                lastmod = article.published_at or article.updated_at
                if lastmod:
                    lastmod_utc = lastmod.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    lastmod_utc = timezone.now().astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                
                # Підготовляємо метадані для Google News
                urlset.append({
                    'location': request.build_absolute_uri(location),
                    'lastmod': lastmod_utc,
                    'news_title': article.get_title(self.language),
                    'news_keywords': self._get_keywords(article, self.language),
                })
            
            # Рендеримо template
            content = render_to_string('news/google_news_sitemap.xml', {
                'urlset': urlset,
                'language': self.language
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
    
    def _get_keywords(self, article, language='uk'):
        """Отримує ключові слова для статті на конкретній мові"""
        keywords = []
        
        # Додаємо категорію
        if article.category:
            keywords.append(article.category.get_name(language))
        
        # Додаємо теги
        if hasattr(article, 'tags') and article.tags.exists():
            keywords.extend([tag.get_name(language) for tag in article.tags.all()])
        
        # Додаємо ключові слова з RSS категорії
        if hasattr(article, 'raw_article') and article.raw_article.source:
            rss_category = article.raw_article.source.get_category_display()
            if rss_category:
                keywords.append(rss_category)
        
        # Додаємо специфічні ключові слова на основі контенту
        content_keywords = self._extract_content_keywords(article, language)
        keywords.extend(content_keywords)
        
        # Видаляємо дублікати та обмежуємо кількість
        unique_keywords = list(dict.fromkeys(keywords))[:8]  # Максимум 8 ключових слів
        return ', '.join(unique_keywords)
    
    def _extract_content_keywords(self, article, language='uk'):
        """Витягує ключові слова з контенту статті"""
        keywords = []
        
        # Аналізуємо заголовок та контент
        title = article.get_title(language).lower()
        content = article.get_summary(language).lower()
        
        # Специфічні ключові слова для технологій
        tech_keywords = {
            'uk': ['AI', 'штучний інтелект', 'автоматизація', 'технології', 'бізнес', 'розробка', 'інновації'],
            'pl': ['AI', 'sztuczna inteligencja', 'automatyzacja', 'technologie', 'biznes', 'rozwój', 'innowacje'],
            'en': ['AI', 'artificial intelligence', 'automation', 'technology', 'business', 'development', 'innovation']
        }
        
        # Шукаємо ключові слова в контенті
        for keyword in tech_keywords.get(language, tech_keywords['uk']):
            if keyword.lower() in title or keyword.lower() in content:
                keywords.append(keyword)
        
        return keywords


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
