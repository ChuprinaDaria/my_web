from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count
from django.utils.translation import get_language
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView
from django.contrib.sitemaps import Sitemap
from datetime import datetime, timedelta

from .models import ProcessedArticle, NewsCategory, DailyDigest


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


class ArticleDetailView(DetailView):
    """Детальна сторінка статті з SEO"""
    model = ProcessedArticle
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    
    def get_object(self, queryset=None):
        """Отримуємо статтю та збільшуємо лічильник переглядів"""
        article = super().get_object(queryset)
        
        if article.status != 'published':
            raise Http404("Стаття не опублікована")
        
        # Збільшуємо лічильник переглядів
        language = get_language() or 'uk'
        article.increment_views(language)
        
        return article
    
    def get_context_data(self, **kwargs):
        """SEO контекст"""
        context = super().get_context_data(**kwargs)
        article = context['article']
        language = get_language() or 'uk'
        
        # SEO метадані
        context['page_title'] = article.get_meta_title(language) or article.get_title(language)
        context['page_description'] = article.get_meta_description(language) or article.get_summary(language)[:160]
        
        # Open Graph метадані
        context['og_title'] = article.get_title(language)
        context['og_description'] = article.get_summary(language)[:200]
        context['og_image'] = article.ai_image_url
        context['og_url'] = self.request.build_absolute_uri()
        
        # Схожі статті
        context['related_articles'] = ProcessedArticle.objects.filter(
            category=article.category,
            status='published'
        ).exclude(id=article.id).order_by('-published_at')[:3]
        
        # Structured data
        context['structured_data'] = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": article.get_title(language),
            "description": article.get_summary(language),
            "articleBody": article.get_business_insight(language),
            "url": self.request.build_absolute_uri(),
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
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": self.request.build_absolute_uri()
            }
        }
        
        if article.ai_image_url:
            context['structured_data']['image'] = article.ai_image_url
        
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