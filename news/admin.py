# СУПЕР ПРОСТИЙ admin.py - БЕЗ ЖОДНИХ ЗАМОРОЧОК!

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils.translation import override

from .models import (
    RSSSource, 
    NewsCategory, 
    RawArticle, 
    ProcessedArticle,
    ROIAnalytics,
    DailyDigest,
    AIProcessingLog,
    SocialMediaPost,
    NewsWidget
)

# Базові налаштування
admin.site.site_header = "News Admin"
admin.site.site_title = "News"


# === ROI ANALYTICS (НАЙПРОСТІШИЙ) ===
@admin.register(ROIAnalytics)
class SimpleROIAdmin(admin.ModelAdmin):
    list_display = [
        'date', 
        'articles_processed', 
        'show_savings',
        'show_roi',
        'tags_assigned'
    ]
    
    list_filter = ['date']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']
    
    def show_savings(self, obj):
        try:
            savings = obj.net_savings
            return str(savings)
        except:
            return "0"
    show_savings.short_description = "Економія"
    
    def show_roi(self, obj):
        try:
            roi = obj.roi_percentage
            return str(roi) + "%"
        except:
            return "0%"
    show_roi.short_description = "ROI"


# === СТАТТІ (НАЙПРОСТІШІ) ===
@admin.register(ProcessedArticle)
class SimpleArticleAdmin(admin.ModelAdmin):
    list_display = ['get_title', 'category', 'status', 'priority', 'show_ai_cost', 'show_ai_time', 'show_ai_ops', 'created_at']
    list_filter = ['status', 'category', 'priority']
    search_fields = ['title_uk', 'title_en', 'title_pl']
    readonly_fields = ['created_at', 'updated_at', 'ai_image_url', 'get_original_content', 'get_original_summary', 'get_original_url', 'show_ai_cost', 'show_ai_time', 'show_ai_ops']
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('status', 'priority', 'category')
        }),
        ('Заголовки', {
            'fields': ('title_en', 'title_uk', 'title_pl')
        }),
        ('Повний контент', {
            'fields': ('summary_en', 'summary_uk', 'summary_pl'),
            'classes': ('wide',)
        }),
        ('Оригінальний контент', {
            'fields': ('get_original_content', 'get_original_summary', 'get_original_url'),
            'classes': ('wide', 'collapse')
        }),
        ('Бізнес інсайти', {
            'fields': ('business_insight_en', 'business_insight_uk', 'business_insight_pl'),
            'classes': ('wide',)
        }),
        ('AI Метадані', {
            'fields': ('show_ai_cost', 'show_ai_time', 'show_ai_ops'),
            'classes': ('collapse',)
        }),
        ('Метадані', {
            'fields': ('ai_image_url', 'published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_title(self, obj):
        return obj.title_uk or obj.title_en or "Без назви"
    get_title.short_description = "Назва"
    
    def get_original_content(self, obj):
        """Повертає оригінальний контент статті"""
        if obj.raw_article and obj.raw_article.content:
            return obj.raw_article.content[:500] + "..." if len(obj.raw_article.content) > 500 else obj.raw_article.content
        return "Немає контенту"
    get_original_content.short_description = 'Оригінальний контент'
    
    def get_original_summary(self, obj):
        """Повертає оригінальний короткий опис"""
        if obj.raw_article and obj.raw_article.summary:
            return obj.raw_article.summary
        return "Немає опису"
    get_original_summary.short_description = 'Оригінальний опис'
    
    def get_original_url(self, obj):
        """Повертає посилання на оригінальну статтю"""
        if obj.raw_article and obj.raw_article.original_url:
            return obj.raw_article.original_url
        return "Немає посилання"
    get_original_url.short_description = 'Оригінальне посилання'
    
    def show_ai_cost(self, obj):
        """Показує вартість AI обробки"""
        cost = obj.get_ai_processing_cost()
        if cost > 0:
            return f"${cost:.4f}"
        return "N/A"
    show_ai_cost.short_description = "AI Вартість"
    show_ai_cost.admin_order_field = 'ai_cost'
    
    def show_ai_time(self, obj):
        """Показує час AI обробки"""
        time = obj.get_ai_processing_time()
        if time > 0:
            return f"{time:.1f}с"
        return "N/A"
    show_ai_time.short_description = "AI Час"
    
    def show_ai_ops(self, obj):
        """Показує кількість AI операцій"""
        ops = obj.get_ai_operations_count()
        if ops > 0:
            return f"{ops} оп."
        return "N/A"
    show_ai_ops.short_description = "AI Операції"


# === AI PROCESSING LOGS ===
@admin.register(AIProcessingLog)
class AIProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['article', 'log_type', 'model_used', 'show_cost', 'show_time', 'success', 'created_at']
    list_filter = ['log_type', 'model_used', 'success', 'created_at']
    search_fields = ['article__title', 'model_used']
    readonly_fields = ['created_at', 'input_tokens', 'output_tokens', 'processing_time', 'cost']
    ordering = ['-created_at']
    
    def show_cost(self, obj):
        """Показує вартість операції"""
        return f"${obj.cost:.6f}"
    show_cost.short_description = "Вартість"
    show_cost.admin_order_field = 'cost'
    
    def show_time(self, obj):
        """Показує час обробки"""
        return f"{obj.processing_time:.2f}с"
    show_time.short_description = "Час"
    show_time.admin_order_field = 'processing_time'


# === RSS ДЖЕРЕЛА ===
@admin.register(RSSSource)
class SimpleRSSAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'is_active']
    list_filter = ['language', 'is_active']


# === КАТЕГОРІЇ ===
@admin.register(NewsCategory)
class SimpleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name_uk', 'is_active']
    list_editable = ['is_active']
    autocomplete_fields = ['cta_service']
    fieldsets = (
        ('Основне', {
            'fields': ('slug', 'is_active', 'order')
        }),
        ('Назви', {
            'fields': ('name_uk', 'name_pl', 'name_en')
        }),
        ('Описи', {
            'fields': ('description_uk', 'description_pl', 'description_en')
        }),
        ('CTA', {
            'fields': (
                'cta_title_uk','cta_title_pl','cta_title_en',
                'cta_description_uk','cta_description_pl','cta_description_en',
                'cta_service','cta_url_preview'
            )
        }),
    )
    readonly_fields = ['cta_url_preview']

    def cta_url_preview(self, obj):
        if not obj or not getattr(obj, 'cta_service', None):
            return "—"
        parts = []
        try:
            with override('uk'):
                parts.append(f"UK: <code>{obj.get_cta_url('uk')}</code>")
            with override('pl'):
                parts.append(f"PL: <code>{obj.get_cta_url('pl')}</code>")
            with override('en'):
                parts.append(f"EN: <code>{obj.get_cta_url('en')}</code>")
        except Exception:
            return obj.get_cta_url() or "—"
        return format_html('<br>'.join(parts))
    cta_url_preview.short_description = "CTA URL (uk/pl/en)"


# === СИРІ СТАТТІ (ТІЛЬКИ ЧИТАННЯ) ===
@admin.register(RawArticle)
class SimpleRawAdmin(admin.ModelAdmin):
    list_display = ['get_title', 'source', 'is_processed']
    readonly_fields = ['title', 'content', 'fetched_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_title(self, obj):
        title = obj.title
        if len(title) > 50:
            return title[:50] + "..."
        return title
    get_title.short_description = "Назва"


# === AI ЛОГИ (видалено - використовується новий AIProcessingLogAdmin) ===


# === СОЦМЕРЕЖІ ===
@admin.register(SocialMediaPost)
class SimpleSocialAdmin(admin.ModelAdmin):
    list_display = ['platform', 'get_article', 'status']
    list_filter = ['platform', 'status']
    
    def get_article(self, obj):
        title = obj.article.title_uk
        if len(title) > 30:
            return title[:30] + "..."
        return title
    get_article.short_description = "Стаття"


# === ДАЙДЖЕСТИ ===
@admin.register(DailyDigest)
class SimpleDaigestAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_articles', 'is_published']
    list_filter = ['is_published']
    
    def has_add_permission(self, request):
        return False


# === ВІДЖЕТИ ===
@admin.register(NewsWidget)
class SimpleWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'widget_type', 'is_active']
    list_editable = ['is_active']


# КІНЕЦЬ - БІЛЬШЕ НІЧОГО!