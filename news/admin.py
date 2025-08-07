from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Avg, Q 
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    RSSSource, NewsCategory, RawArticle, ProcessedArticle, 
    DailyDigest, AIProcessingLog, TranslationCache
)


@admin.register(RSSSource)
class RSSSourceAdmin(admin.ModelAdmin):
    """RSS джерела - налаштування та моніторинг"""
    list_display = [
        'name', 'language', 'category', 'is_active', 
        'last_fetched', 'articles_today', 'fetch_status'
    ]
    list_filter = ['language', 'category', 'is_active', 'last_fetched']
    search_fields = ['name', 'url', 'description']
    readonly_fields = ['last_fetched', 'created_at']
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('name', 'url', 'language', 'category', 'description')
        }),
        (_('Налаштування'), {
            'fields': ('is_active', 'fetch_frequency')
        }),
        (_('Статистика'), {
            'fields': ('last_fetched', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def articles_today(self, obj):
        """Кількість статей сьогодні"""
        today = timezone.now().date()
        count = obj.raw_articles.filter(fetched_at__date=today).count()
        if count > 0:
            return format_html('<span style="color: green;">📈 {}</span>', count)
        return format_html('<span style="color: orange;">⚠️ 0</span>')
    articles_today.short_description = _('Статей сьогодні')
    
    def fetch_status(self, obj):
        """Статус останнього оновлення"""
        if not obj.last_fetched:
            return format_html('<span style="color: red;">❌ Ніколи</span>')
        
        time_diff = timezone.now() - obj.last_fetched
        if time_diff < timedelta(hours=2):
            return format_html('<span style="color: green;">✅ Свіжий</span>')
        elif time_diff < timedelta(hours=24):
            return format_html('<span style="color: orange;">⚠️ Старий</span>')
        else:
            return format_html('<span style="color: red;">❌ Мертвий</span>')
    fetch_status.short_description = _('Статус')


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    """Категорії новин - налаштування CTA"""
    list_display = ['icon', 'name_uk', 'articles_count', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name_en', 'name_pl', 'name_uk']
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('slug', 'icon', 'color', 'order', 'is_active')
        }),
        (_('Назви (тримовні)'), {
            'fields': ('name_en', 'name_pl', 'name_uk')
        }),
        (_('Описи (тримовні)'), {
            'fields': ('description_en', 'description_pl', 'description_uk'),
            'classes': ('collapse',)
        }),
        (_('CTA Заголовки'), {
            'fields': ('cta_title_en', 'cta_title_pl', 'cta_title_uk'),
            'classes': ('collapse',)
        }),
        (_('CTA Описи'), {
            'fields': ('cta_description_en', 'cta_description_pl', 'cta_description_uk'),
            'classes': ('collapse',)
        }),
        (_('CTA Кнопки'), {
            'fields': ('cta_button_text_en', 'cta_button_text_pl', 'cta_button_text_uk', 'cta_link'),
            'classes': ('collapse',)
        }),
    )
    
    def articles_count(self, obj):
        """Кількість статей в категорії"""
        count = obj.articles.filter(status='published').count()
        return format_html('<span style="color: blue;">📊 {}</span>', count)
    articles_count.short_description = _('Статей')


@admin.register(RawArticle)
class RawArticleAdmin(admin.ModelAdmin):
    """Сирі статті - тільки перегляд"""
    list_display = [
        'title_short', 'source', 'published_at', 'fetched_at', 
        'processing_status', 'is_duplicate'
    ]
    list_filter = [
        'source__language', 'source__category', 'is_processed', 
        'is_duplicate', 'fetched_at'
    ]
    search_fields = ['title', 'content', 'author']
    readonly_fields = [
        'uuid', 'title', 'content', 'summary', 'original_url', 'author',
        'published_at', 'fetched_at', 'content_hash', 'error_message'
    ]
    
    # Заборона редагування
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False  # Тільки читання
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Тільки суперюзер може видаляти
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('uuid', 'source', 'title', 'author', 'published_at')
        }),
        (_('Контент'), {
            'fields': ('summary', 'content'),
            'classes': ('collapse',)
        }),
        (_('Метадані'), {
            'fields': ('original_url', 'fetched_at', 'content_hash'),
            'classes': ('collapse',)
        }),
        (_('Обробка'), {
            'fields': ('is_processed', 'is_duplicate', 'processing_attempts', 'error_message'),
        }),
    )
    
    def title_short(self, obj):
        """Короткий заголовок"""
        return obj.title[:80] + '...' if len(obj.title) > 80 else obj.title
    title_short.short_description = _('Заголовок')
    
    def processing_status(self, obj):
        """Статус обробки"""
        if obj.is_duplicate:
            return format_html('<span style="color: orange;">🔄 Дублікат</span>')
        elif obj.is_processed:
            return format_html('<span style="color: green;">✅ Оброблено</span>')
        elif obj.processing_attempts > 0:
            return format_html('<span style="color: red;">❌ Помилка</span>')
        else:
            return format_html('<span style="color: blue;">⏳ Очікує</span>')
    processing_status.short_description = _('Статус')


@admin.register(ProcessedArticle)
class ProcessedArticleAdmin(admin.ModelAdmin):
    """Оброблені статті - моніторинг результатів AI"""
    list_display = [
        'title_uk_short', 'category', 'status', 'priority', 
        'total_views', 'ai_cost', 'published_at'
    ]
    list_filter = [
        'status', 'category', 'priority', 'raw_article__source__language',
        'published_at', 'ai_model_used'
    ]
    search_fields = ['title_en', 'title_pl', 'title_uk', 'summary_uk']
    readonly_fields = [
        'uuid', 'raw_article', 'created_at', 'updated_at', 'published_at',
        'ai_model_used', 'ai_cost', 'ai_processing_time', 'get_total_views'
    ]
    
    # Дозволяємо тільки зміну статусу та пріоритету
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Редагування існуючого об'єкта
            return self.readonly_fields + [
                'title_en', 'title_pl', 'title_uk',
                'summary_en', 'summary_pl', 'summary_uk',
                'business_insight_en', 'business_insight_pl', 'business_insight_uk',
                'category', 'key_takeaways_en', 'key_takeaways_pl', 'key_takeaways_uk'
            ]
        return self.readonly_fields
    
    def has_add_permission(self, request):
        return False  # AI створює статті
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('uuid', 'raw_article', 'category', 'status', 'priority')
        }),
        (_('Заголовки (тримовні)'), {
            'fields': ('title_en', 'title_pl', 'title_uk'),
        }),
        (_('Описи (тримовні)'), {
            'fields': ('summary_en', 'summary_pl', 'summary_uk'),
            'classes': ('collapse',)
        }),
        (_('Бізнес-інсайти (тримовні)'), {
            'fields': ('business_insight_en', 'business_insight_pl', 'business_insight_uk'),
            'classes': ('collapse',)
        }),
        (_('SEO (тримовні)'), {
            'fields': (
                'meta_title_en', 'meta_title_pl', 'meta_title_uk',
                'meta_description_en', 'meta_description_pl', 'meta_description_uk'
            ),
            'classes': ('collapse',)
        }),
        (_('AI Генерація'), {
            'fields': ('ai_image_url', 'ai_model_used', 'ai_cost', 'ai_processing_time'),
            'classes': ('collapse',)
        }),
        (_('Статистика'), {
            'fields': ('views_count_en', 'views_count_pl', 'views_count_uk', 'shares_count'),
            'classes': ('collapse',)
        }),
        (_('Дати'), {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_uk_short(self, obj):
        """Короткий український заголовок"""
        return obj.title_uk[:60] + '...' if len(obj.title_uk) > 60 else obj.title_uk
    title_uk_short.short_description = _('Заголовок (UK)')
    
    def total_views(self, obj):
        """Загальна кількість переглядів"""
        total = obj.get_total_views()
        return format_html(
            '<span style="color: blue;">👁️ {} (🇺🇦{} 🇬🇧{} 🇵🇱{})</span>', 
            total, obj.views_count_uk, obj.views_count_en, obj.views_count_pl
        )
    total_views.short_description = _('Перегляди')


@admin.register(DailyDigest)
class DailyDigestAdmin(admin.ModelAdmin):
    """Щоденні дайджести - моніторинг автогенерації"""
    list_display = ['date', 'total_articles', 'is_generated', 'is_published', 'created_at']
    list_filter = ['is_generated', 'is_published', 'date']
    readonly_fields = [
        'date', 'title_en', 'title_pl', 'title_uk',
        'intro_text_en', 'intro_text_pl', 'intro_text_uk',
        'summary_en', 'summary_pl', 'summary_uk',
        'total_articles', 'top_categories', 'created_at', 'published_at'
    ]
    
    def has_add_permission(self, request):
        return False  # AI створює дайджести
    
    def has_change_permission(self, request, obj=None):
        return False  # Тільки читання
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('date', 'total_articles', 'is_generated', 'is_published')
        }),
        (_('Заголовки (тримовні)'), {
            'fields': ('title_en', 'title_pl', 'title_uk'),
            'classes': ('collapse',)
        }),
        (_('Вступні тексти (тримовні)'), {
            'fields': ('intro_text_en', 'intro_text_pl', 'intro_text_uk'),
            'classes': ('collapse',)
        }),
        (_('Огляди (тримовні)'), {
            'fields': ('summary_en', 'summary_pl', 'summary_uk'),
            'classes': ('collapse',)
        }),
        (_('Статистика'), {
            'fields': ('top_categories', 'created_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIProcessingLog)
class AIProcessingLogAdmin(admin.ModelAdmin):
    """Логи AI обробки - моніторинг витрат та якості"""
    list_display = [
        'log_type', 'model_used', 'target_language', 'success', 
        'processing_time', 'cost', 'created_at'
    ]
    list_filter = [
        'log_type', 'model_used', 'target_language', 'success', 'created_at'
    ]
    search_fields = ['article__title', 'error_message']
    readonly_fields = [
        'article', 'log_type', 'model_used', 'target_language',
        'input_tokens', 'output_tokens', 'input_data', 'output_data',
        'processing_time', 'cost', 'success', 'error_message', 'created_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Тільки суперюзер може видаляти логи
    
    # Додаткові методи для аналітики
    def changelist_view(self, request, extra_context=None):
        """Додати статистику на сторінку списку"""
        # Статистика за останні 30 днів
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        stats = AIProcessingLog.objects.filter(created_at__gte=thirty_days_ago).aggregate(
            total_cost=Sum('cost'),
            avg_processing_time=Avg('processing_time'),
            total_requests=Count('id'),
            successful_requests=Count('id', filter=Q(success=True))
        )
        
        # Статистика по моделях
        model_stats = AIProcessingLog.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('model_used').annotate(
            count=Count('id'),
            total_cost=Sum('cost'),
            avg_time=Avg('processing_time')
        ).order_by('-count')
        
        extra_context = extra_context or {}
        extra_context['stats'] = stats
        extra_context['model_stats'] = model_stats
        
        return super().changelist_view(request, extra_context)


@admin.register(TranslationCache)
class TranslationCacheAdmin(admin.ModelAdmin):
    """Кеш перекладів - моніторинг ефективності"""
    list_display = [
        'source_language', 'target_language', 'translator_used', 
        'used_count', 'quality_score', 'last_used'
    ]
    list_filter = [
        'source_language', 'target_language', 'translator_used', 'created_at'
    ]
    search_fields = ['source_text', 'translated_text']
    readonly_fields = [
        'source_text_hash', 'source_text', 'translated_text', 
        'translator_used', 'created_at', 'used_count', 'last_used'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Кастомна сторінка з аналітикою
class NewsAnalyticsAdmin(admin.ModelAdmin):
    """Кастомна аналітика новинної системи"""
    
    def changelist_view(self, request, extra_context=None):
        """Головна аналітична панель"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Загальна статистика
        total_articles = ProcessedArticle.objects.filter(status='published').count()
        articles_today = ProcessedArticle.objects.filter(published_at__date=today).count()
        articles_week = ProcessedArticle.objects.filter(published_at__date__gte=week_ago).count()
        
        # AI витрати
        ai_cost_month = AIProcessingLog.objects.filter(
            created_at__date__gte=month_ago
        ).aggregate(total=Sum('cost'))['total'] or 0
        
        # Популярні категорії
        popular_categories = ProcessedArticle.objects.filter(
            status='published'
        ).values('category__name_uk').annotate(
            count=Count('id'),
            total_views=Sum('views_count_uk') + Sum('views_count_en') + Sum('views_count_pl')
        ).order_by('-count')[:10]
        
        # RSS джерела статистика
        rss_stats = RSSSource.objects.annotate(
            articles_count=Count('raw_articles'),
            processed_count=Count('raw_articles__processed')
        ).order_by('-articles_count')
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_articles': total_articles,
            'articles_today': articles_today,
            'articles_week': articles_week,
            'ai_cost_month': round(float(ai_cost_month), 2),
            'popular_categories': popular_categories,
            'rss_stats': rss_stats,
        })
        
        return super().changelist_view(request, extra_context)


# Реєструємо кастомну аналітику (використовуючи одну з існуючих моделей)
admin.site.unregister(ProcessedArticle)
admin.site.register(ProcessedArticle, NewsAnalyticsAdmin)