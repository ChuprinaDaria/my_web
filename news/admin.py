# СУПЕР ПРОСТИЙ admin.py - БЕЗ ЖОДНИХ ЗАМОРОЧОК!

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils.translation import override
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.core.management import call_command
from django.utils import timezone
from datetime import datetime
from django.http import HttpResponseRedirect
from django.contrib.admin import helpers
from django.template.response import TemplateResponse

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
        'show_social_posts',
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
    
    def show_social_posts(self, obj):
        try:
            from .models import SocialMediaPost
            posts_count = SocialMediaPost.objects.filter(
                created_at__date=obj.date,
                status='published'
            ).count()
            return f"{posts_count} постів"
        except:
            return "0 постів"
    show_social_posts.short_description = "Соцмережі"


# === СТАТТІ (НАЙПРОСТІШІ) ===
@admin.register(ProcessedArticle)
class SimpleArticleAdmin(admin.ModelAdmin):
    list_display = ['get_title', 'category', 'status', 'priority', 'is_top_article', 'article_rank', 'show_ai_cost', 'show_ai_time', 'show_ai_ops', 'show_social_posts', 'telegram_publish_button', 'created_at']
    list_filter = ['status', 'category', 'priority', 'is_top_article']
    search_fields = ['title_uk', 'title_en', 'title_pl']
    readonly_fields = ['created_at', 'updated_at', 'ai_image_url', 'get_original_content', 'get_original_summary', 'get_original_url', 'get_full_content_uk', 'show_ai_cost', 'show_ai_time', 'show_ai_ops', 'show_social_posts', 'telegram_publish_button']
    actions = ['publish_to_telegram']
    
    def publish_single_to_telegram(self, request, article_id):
        """Публікує одну статтю в Telegram"""
        try:
            article = ProcessedArticle.objects.get(pk=article_id)
            
            # Перевіряємо чи вже опубліковано
            if article.social_posts.filter(platform='telegram_uk', status='published').exists():
                messages.warning(request, '⚠️ Стаття вже опублікована в Telegram')
                return redirect('..')
            
            # Створюємо повідомлення з українським контентом
            # Якщо title_uk такий же як title_en (англійський), використовуємо business_insight_uk для заголовка
            if article.title_uk == article.title_en and article.business_insight_uk:
                title = article.business_insight_uk[:80] + "..."
            else:
                title = article.title_uk[:80] if article.title_uk else article.title_en[:80]
            
            # Summary - якщо український summary порожній або такий же як англійський, використовуємо business_insight_uk
            if article.summary_uk and article.summary_uk != article.summary_en:
                summary = article.summary_uk[:200]
            elif article.business_insight_uk:
                summary = article.business_insight_uk[:200] + "..."
            else:
                summary = article.summary_en[:200]
            
            message = (
                f"🔥 <strong>{title}</strong>\n\n"
                f"{summary}\n\n"
                f"— <em>Lazysoft AI News</em>"
            )
            
            # Створюємо кнопку "Читати далі"
            button = {"inline_keyboard": [[{"text": "📖 Читати далі", "url": f"https://lazysoft.dev{article.get_absolute_url('uk')}"}]]}
            
            # Публікуємо в Telegram
            from news.services.telegram import TelegramService
            telegram_service = TelegramService()
            external_id = telegram_service.post_to_telegram(
                message, 
                photo_url=article.ai_image_url,
                reply_markup=button
            )
            
            if external_id:
                # Створюємо запис про публікацію
                from news.models import SocialMediaPost
                smp, created = SocialMediaPost.objects.get_or_create(
                    article=article,
                    platform='telegram_uk',
                    defaults={
                        'content': message,
                        'image_url': article.ai_image_url,
                        'status': 'draft'
                    }
                )
                smp.mark_as_published(external_id)
                messages.success(request, f'✅ Статтю "{article.get_title("uk")}" успішно опубліковано в Telegram!')
            else:
                messages.error(request, '❌ Не вдалося опублікувати статтю в Telegram')
                
        except ProcessedArticle.DoesNotExist:
            messages.error(request, '❌ Статтю не знайдено')
        except Exception as e:
            messages.error(request, f'❌ Помилка публікації: {str(e)}')
        
        return redirect('..')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('run-pipeline/', self.admin_site.admin_view(self.run_pipeline), name='news_processedarticle_run_pipeline'),
            path('<int:article_id>/publish-telegram/', self.admin_site.admin_view(self.publish_single_to_telegram), name='news_processedarticle_publish_telegram'),
        ]
        return custom_urls + urls
    
    def run_pipeline(self, request):
        """Запускає повний пайплайн новин"""
        try:
            # Запускаємо management command
            call_command('daily_news_pipeline', '--full-pipeline', '--auto-publish', verbosity=1)
            messages.success(request, '✅ Пайплайн успішно запущено! Перевірте логи для деталей.')
        except Exception as e:
            messages.error(request, f'❌ Помилка запуску пайплайну: {str(e)}')
        
        return redirect('..')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['pipeline_button'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def publish_to_telegram(self, request, queryset):
        """Публікує вибрані статті в Telegram"""
        published_count = 0
        errors = []
        
        for article in queryset:
            try:
                # Перевіряємо чи вже опубліковано
                if article.social_posts.filter(platform='telegram_uk', status='published').exists():
                    continue
                
                # Створюємо повідомлення з українським контентом
                # Якщо title_uk такий же як title_en (англійський), використовуємо business_insight_uk для заголовка
                if article.title_uk == article.title_en and article.business_insight_uk:
                    title = article.business_insight_uk[:80] + "..."
                else:
                    title = article.title_uk[:80] if article.title_uk else article.title_en[:80]
                
                # Summary - якщо український summary порожній або такий же як англійський, використовуємо business_insight_uk
                if article.summary_uk and article.summary_uk != article.summary_en:
                    summary = article.summary_uk[:200]
                elif article.business_insight_uk:
                    summary = article.business_insight_uk[:200] + "..."
                else:
                    summary = article.summary_en[:200]
                
                message = (
                    f"🔥 <strong>{title}</strong>\n\n"
                    f"{summary}\n\n"
                    f"— <em>Lazysoft AI News</em>"
                )
                
                # Створюємо кнопку "Читати далі"
                button = {"inline_keyboard": [[{"text": "📖 Читати далі", "url": f"https://lazysoft.dev{article.get_absolute_url('uk')}"}]]}
                
                # Публікуємо в Telegram
                from news.services.telegram import TelegramService
                telegram_service = TelegramService()
                external_id = telegram_service.post_to_telegram(
                    message, 
                    photo_url=article.ai_image_url,
                    reply_markup=button
                )
                
                if external_id:
                    # Створюємо запис про публікацію
                    from news.models import SocialMediaPost
                    smp, created = SocialMediaPost.objects.get_or_create(
                        article=article,
                        platform='telegram_uk',
                        defaults={
                            'content': message,
                            'image_url': article.ai_image_url,
                            'status': 'draft'
                        }
                    )
                    smp.mark_as_published(external_id)
                    published_count += 1
                else:
                    errors.append(f"Не вдалося опублікувати: {article.get_title('uk')[:50]}...")
                    
            except Exception as e:
                errors.append(f"Помилка для {article.get_title('uk')[:50]}...: {str(e)}")
        
        if published_count > 0:
            messages.success(request, f'✅ Опубліковано {published_count} статей в Telegram')
        if errors:
            for error in errors[:5]:  # Показуємо максимум 5 помилок
                messages.warning(request, f'⚠️ {error}')
        
        return HttpResponseRedirect(request.get_full_path())
    
    publish_to_telegram.short_description = "📢 Опублікувати в Telegram"
    
    def telegram_publish_button(self, obj):
        """Кнопка для публікації в Telegram з деталей статті"""
        if obj.pk:
            # Перевіряємо чи вже опубліковано
            if obj.social_posts.filter(platform='telegram_uk', status='published').exists():
                return format_html(
                    '<span style="color: green;">✅ Вже опубліковано в Telegram</span>'
                )
            else:
                return format_html(
                    '<a href="{}" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">📢 Опублікувати в Telegram</a>',
                    reverse('admin:news_processedarticle_publish_telegram', args=[obj.pk])
                )
        return "-"
    
    telegram_publish_button.short_description = "Telegram"
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('status', 'priority', 'category', 'is_top_article', 'article_rank')
        }),
        ('Заголовки', {
            'fields': ('title_en', 'title_uk', 'title_pl')
        }),
        ('Повний контент', {
            'fields': ('summary_en', 'summary_uk', 'summary_pl'),
            'classes': ('wide',)
        }),
        ('Оригінальний контент', {
            'fields': ('get_original_content', 'get_original_summary', 'get_original_url', 'get_full_content_uk'),
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
        ('Telegram', {
            'fields': ('telegram_publish_button',),
            'classes': ('wide',)
        }),
    )
    
    def get_title(self, obj):
        return obj.title_uk or obj.title_en or "Без назви"
    get_title.short_description = "Назва"
    
    def get_original_content(self, obj):
        """Повертає оригінальний контент статті"""
        if obj.raw_article and obj.raw_article.content:
            return mark_safe(f'<div style="max-height: 500px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9;">{obj.raw_article.content}</div>')
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
    
    def get_full_content_uk(self, obj):
        """Повертає повний контент українською (якщо є)"""
        if obj.full_content_uk:
            return mark_safe(f'<div style="max-height: 500px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f0f8ff;">{obj.full_content_uk}</div>')
        return "Немає повного контенту"
    get_full_content_uk.short_description = 'Повний контент (UK)'
    
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
    
    def show_social_posts(self, obj):
        """Показує кількість постів в соцмережах для цієї статті"""
        try:
            posts_count = obj.social_posts.filter(status='published').count()
            if posts_count > 0:
                return f"{posts_count} постів"
            return "0 постів"
        except:
            return "0 постів"
    show_social_posts.short_description = "Соцмережі"


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