# rag/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django import forms

from .models import (
    EmbeddingModel, ChatSession, ChatMessage, 
    RAGAnalytics, KnowledgeSource
)
from .services import IndexingService
from .learning import LearningPattern, DialogAnalyzer


@admin.register(EmbeddingModel)
class EmbeddingModelAdmin(admin.ModelAdmin):
    list_display = (
        'content_title_short',
        'content_type_badge',
        'language_badge', 
        'model_name',
        'is_active',
        'created_at'
    )
    list_filter = (
        'content_type',
        'language',
        'content_category',
        'model_name',
        'is_active',
        'created_at'
    )
    search_fields = ('content_title', 'content_text')
    readonly_fields = ('embedding', 'created_at', 'updated_at')
    ordering = ['-created_at']
    
    fieldsets = (
        ("🎯 Основна інформація", {
            'fields': (
                ('content_type', 'object_id'),
                ('content_title', 'content_category'),
                ('language', 'is_active')
            )
        }),
        ("📝 Контент", {
            'fields': ('content_text',),
            'classes': ('collapse',)
        }),
        ("🤖 AI метадані", {
            'fields': (
                ('model_name', 'embedding_version'),
                'tags',
                'metadata'
            ),
            'classes': ('collapse',)
        }),
        ("🔢 Векторні дані", {
            'fields': ('embedding',),
            'classes': ('collapse',),
            'description': "Векторне представлення тексту для пошуку"
        }),
        ("📅 Дати", {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',)
        })
    )
    
    def content_title_short(self, obj):
        """Скорочений заголовок"""
        title = obj.content_title or ""
        return (title[:50] + "...") if len(title) > 50 else title
    content_title_short.short_description = '📝 Заголовок'
    content_title_short.admin_order_field = 'content_title'
    
    def content_type_badge(self, obj):
        """Бейдж типу контенту"""
        colors = {
            'service': '#28a745',    # зелений
            'project': '#007bff',    # синій  
            'faq': '#ffc107',        # жовтий
            'manual': '#6c757d'      # сірий
        }
        category = (obj.content_category or '').strip()
        color = colors.get(category, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, category.upper() if category else '-'
        )
    content_type_badge.short_description = '🗂️ Тип'
    
    def language_badge(self, obj):
        """Бейдж мови"""
        colors = {'uk': '#0057B7', 'en': '#00A300', 'pl': '#DC143C'}  # Кольори прапорів
        lang = (obj.language or '').lower()
        color = colors.get(lang, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;">{}</span>',
            color, (lang.upper() if lang else '-')
        )
    language_badge.short_description = '🌍 Мова'
    
    actions = ['reindex_selected', 'run_index_knowledge']
    
    def reindex_selected(self, request, queryset):
        """Переіндексує обрані об'єкти"""
        indexing_service = IndexingService()
        count = 0
        
        for embedding in queryset:
            if embedding.content_object:
                try:
                    indexing_service.reindex_object(embedding.content_object)
                    count += 1
                except Exception as e:
                    messages.error(request, f"Помилка переіндексації {embedding}: {e}")
        
        messages.success(request, f"Переіндексовано {count} об'єктів")
    reindex_selected.short_description = "🔄 Переіндексувати обрані"

    def run_index_knowledge(self, request, queryset):
        if request.method != 'POST' or request.POST.get('action') != 'run_index_knowledge':
            messages.error(request, "Невірний виклик дії. Будь ласка, запустіть через action-меню.")
            return
        service = IndexingService()
        total_indexed = 0
        deleted_count = 0
        reindex = bool(request.POST.get('reindex')) if 'reindex' in request.POST else False
        cleanup = bool(request.POST.get('cleanup')) if 'cleanup' in request.POST else False
        model_path = (request.POST.get('model') or '').strip() if 'model' in request.POST else ''

        try:
            if model_path:
                app_label, model_name = model_path.split('.')
                ct = ContentType.objects.get(app_label=app_label, model=model_name.lower())
                model_cls = ct.model_class()
                languages = getattr(service, 'rag_settings', {}).get('SUPPORTED_LANGUAGES', ['uk'])
                queryset = model_cls.objects.filter(is_active=True) if hasattr(model_cls, 'is_active') else model_cls.objects.all()
                for obj in queryset:
                    for lang in languages:
                        service.embedding_service.create_embedding_for_object(obj, lang)
                        total_indexed += 1
                messages.success(request, f"Проіндексовано {total_indexed} записів для {model_path}")
            else:
                total_indexed = service.index_all_content()
                messages.success(request, f"Проіндексовано {total_indexed} записів")
        except Exception as e:
            messages.error(request, f"Помилка індексації: {e}")

        if cleanup:
            try:
                deleted_count = service.cleanup_orphaned_embeddings()
                messages.info(request, f"Видалено {deleted_count} застарілих embeddings")
            except Exception as e:
                messages.error(request, f"Помилка очищення embeddings: {e}")

    run_index_knowledge.short_description = "⚙️ Запустити індексацію знань…"


@admin.register(ChatSession) 
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        'session_id_short',
        'client_info',
        'intent_badge',
        'service_category_link',
        'stats_display',
        'lead_status',
        'started_at'
    )
    list_filter = (
        'detected_intent',
        'detected_service_category', 
        'lead_generated',
        'quote_requested',
        'consultation_requested',
        'started_at'
    )
    search_fields = ('session_id', 'client_email', 'client_name')
    readonly_fields = ('started_at', 'last_activity')
    ordering = ['-started_at']
    
    fieldsets = (
        ("👤 Сесія", {
            'fields': (
                'session_id',
                ('client_email', 'client_name'),
                'client_ip'
            )
        }),
        ("🎯 Аналіз AI", {
            'fields': (
                ('detected_intent', 'detected_service_category'),
            )
        }),
        ("📊 Статистика", {
            'fields': (
                ('total_messages', 'total_ai_cost'),
                ('lead_generated', 'quote_requested', 'consultation_requested')
            )
        }),
        ("📅 Дати", {
            'fields': (
                ('started_at', 'last_activity', 'ended_at')
            ),
            'classes': ('collapse',)
        })
    )
    
    def session_id_short(self, obj):
        return obj.session_id[:12] + "..." if len(obj.session_id) > 12 else obj.session_id
    session_id_short.short_description = '🆔 ID сесії'
    
    def client_info(self, obj):
        if obj.client_name and obj.client_email:
            return f"{obj.client_name} ({obj.client_email})"
        elif obj.client_email:
            return obj.client_email
        elif obj.client_name:
            return obj.client_name
        return f"IP: {obj.client_ip or 'невідомий'}"
    client_info.short_description = '👤 Клієнт'
    
    def intent_badge(self, obj):
        colors = {
            'pricing': '#28a745',
            'services': '#007bff', 
            'portfolio': '#6f42c1',
            'consultation': '#fd7e14',
            'general': '#6c757d'
        }
        color = colors.get(obj.detected_intent, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_detected_intent_display()
        )
    intent_badge.short_description = '🎯 Намір'
    
    def service_category_link(self, obj):
        if obj.detected_service_category:
            url = reverse('admin:services_servicecategory_change', args=[obj.detected_service_category.pk])
            return format_html('<a href="{}">{}</a>', url, obj.detected_service_category.title_en)
        return '-'
    service_category_link.short_description = '🗂️ Сервіс'
    
    def stats_display(self, obj):
        return f"💬 {obj.total_messages} | 💰 ${obj.total_ai_cost:.4f}"
    stats_display.short_description = '📊 Статистика'
    
    def lead_status(self, obj):
        status_icons = []
        if obj.lead_generated: status_icons.append('🎯')
        if obj.quote_requested: status_icons.append('💰')  
        if obj.consultation_requested: status_icons.append('📅')
        
        return ''.join(status_icons) or '⭕'
    lead_status.short_description = '🏆 Статус'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        'session_link', 
        'role_badge',
        'content_preview',
        'ai_info',
        'created_at'
    )
    list_filter = (
        'role',
        'ai_model_used',
        'session__detected_intent',
        'created_at'
    )
    search_fields = ('content', 'session__session_id')
    readonly_fields = ('created_at', 'processing_time', 'cost')
    ordering = ['-created_at']
    
    def session_link(self, obj):
        url = reverse('admin:rag_chatsession_change', args=[obj.session.pk])
        return format_html('<a href="{}">{}</a>', url, obj.session.session_id[:12])
    session_link.short_description = '🆔 Сесія'
    
    def role_badge(self, obj):
        colors = {'user': '#007bff', 'assistant': '#28a745', 'system': '#6c757d'}
        color = colors.get(obj.role, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = '👤 Роль'
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = '💬 Повідомлення'
    
    def ai_info(self, obj):
        if obj.role == 'assistant':
            sources_count = len(obj.rag_sources_used) if obj.rag_sources_used else 0
            return f"🤖 {obj.ai_model_used} | 📚 {sources_count} джерел | 💰 ${obj.cost:.4f}"
        return '-'
    ai_info.short_description = '🤖 AI інфо'


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'source_type_badge',
        'priority',
        'auto_update',
        'last_embedding_update',
        'is_active'
    )
    list_editable = ('priority', 'auto_update', 'is_active')
    list_filter = ('source_type', 'auto_update', 'is_active', 'priority')
    search_fields = ('title', 'content_uk')
    ordering = ['priority', '-updated_at']
    
    fieldsets = (
        ("📝 Основна інформація", {
            'fields': (
                ('title', 'source_type'),
                ('priority', 'is_active', 'auto_update')
            )
        }),
        ("📄 Контент (українською)", {
            'fields': ('content_uk',)
        }),
        ("📄 Контент (інші мови)", {
            'fields': ('content_en', 'content_pl'),
            'classes': ('collapse',)
        }),
        ("🏷️ Теги та метадані", {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
        ("🤖 Індексація", {
            'fields': ('last_embedding_update',),
            'classes': ('collapse',)
        })
    )
    
    def source_type_badge(self, obj):
        colors = {
            'service': '#28a745',
            'project': '#007bff',
            'faq': '#ffc107', 
            'manual': '#6c757d'
        }
        color = colors.get(obj.source_type, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_source_type_display()
        )
    source_type_badge.short_description = '🗂️ Тип'
    
    def priority_display(self, obj):
        if obj.priority <= 3:
            color = '#dc3545'  # червоний - високий
            icon = '🔴'
        elif obj.priority <= 6:
            color = '#ffc107'  # жовтий - середній
            icon = '🟡'
        else:
            color = '#28a745'  # зелений - низький
            icon = '🟢'
        
        return format_html(
            '{} <span style="color: {}; font-weight: bold;">{}</span>',
            icon, color, obj.priority
        )
    priority_display.short_description = '⚡ Пріоритет'
    
    actions = ['generate_embeddings']
    
    def generate_embeddings(self, request, queryset):
        """Генерує embeddings для обраних джерел"""
        indexing_service = IndexingService()
        count = 0
        
        for source in queryset:
            try:
                indexing_service.reindex_object(source)
                count += 1
            except Exception as e:
                messages.error(request, f"Помилка індексації {source}: {e}")
        
        messages.success(request, f"Згенеровано embeddings для {count} джерел")
    generate_embeddings.short_description = "🔄 Згенерувати embeddings"


@admin.register(RAGAnalytics)
class RAGAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'searches_stats',
        'cost_display',
        'conversion_stats'
    )
    list_filter = ('date',)
    date_hierarchy = 'date'
    ordering = ['-date']
    
    def searches_stats(self, obj):
        success_rate = (obj.successful_searches / obj.total_searches * 100) if obj.total_searches > 0 else 0
        return format_html(
            '🔍 {} ({}% успішних)',
            obj.total_searches,
            round(success_rate, 1)
        )
    searches_stats.short_description = '🔍 Пошуки'
    
    def cost_display(self, obj):
        return f"💰 ${obj.total_ai_cost:.4f}"
    cost_display.short_description = '💰 Витрати'
    
    def conversion_stats(self, obj):
        return format_html(
            '🎯 {} лідів | 💰 {} прорахунків | 📅 {} консультацій',
            obj.total_leads,
            obj.total_quotes, 
            obj.total_consultations
        )
    conversion_stats.short_description = '📈 Конверсії'


@admin.register(LearningPattern)
class LearningPatternAdmin(admin.ModelAdmin):
    list_display = (
        'query_preview',
        'status_badge', 
        'frequency',
        'success_rate_display',
        'detected_intent',
        'created_at',
        'actions_column'
    )
    list_filter = (
        'status',
        'detected_intent',
        'response_source',
        'created_at'
    )
    search_fields = ('user_query_pattern', 'best_response', 'keywords')
    readonly_fields = ('frequency', 'success_rate', 'created_at', 'updated_at')
    ordering = ['-frequency', '-success_rate', '-created_at']
    
    fieldsets = (
        ("📝 Паттерн запиту", {
            'fields': (
                'user_query_pattern',
                'query_variations',
                ('detected_intent', 'keywords')
            )
        }),
        ("💬 Найкраща відповідь", {
            'fields': (
                'best_response',
                'response_source'
            )
        }),
        ("📊 Метрики", {
            'fields': (
                ('frequency', 'success_rate'),
                'avg_user_satisfaction',
                'related_service_categories'
            ),
            'classes': ('collapse',)
        }),
        ("⚡ Статус", {
            'fields': (
                ('status', 'reviewed_by'),
                ('created_at', 'updated_at')
            )
        })
    )
    
    def query_preview(self, obj):
        return obj.user_query_pattern[:80] + "..." if len(obj.user_query_pattern) > 80 else obj.user_query_pattern
    query_preview.short_description = '❓ Запит'
    
    def status_badge(self, obj):
        colors = {
            'detected': '#6c757d',
            'pending_review': '#ffc107',
            'approved': '#28a745', 
            'indexed': '#007bff',
            'rejected': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '📊 Статус'
    
    def success_rate_display(self, obj):
        if obj.success_rate > 0.8:
            color = '#28a745'  # зелений
            icon = '🟢'
        elif obj.success_rate > 0.5:
            color = '#ffc107'  # жовтий  
            icon = '🟡'
        else:
            color = '#dc3545'  # червоний
            icon = '🔴'
        
        return format_html(
            '{} <span style="color: {}; font-weight: bold;">{:.1%}</span>',
            icon, color, obj.success_rate
        )
    success_rate_display.short_description = '📈 Успішність'
    
    def actions_column(self, obj):
        actions = []
        
        if obj.status == 'pending_review':
            actions.append(
                f'<a href="#" onclick="approvePattern({obj.pk})" style="color: #28a745; margin-right: 10px;">✅ Схвалити</a>'
            )
            actions.append(
                f'<a href="#" onclick="rejectPattern({obj.pk})" style="color: #dc3545;">❌ Відхилити</a>'
            )
        elif obj.status == 'approved':
            actions.append(
                f'<a href="#" onclick="indexPattern({obj.pk})" style="color: #007bff;">📚 Індексувати</a>'
            )
        
        return mark_safe(' | '.join(actions)) if actions else '-'
    actions_column.short_description = '⚡ Дії'
    
    actions = ['approve_selected', 'reject_selected', 'analyze_conversations']
    
    def approve_selected(self, request, queryset):
        """Схвалює обрані паттерни"""
        analyzer = DialogAnalyzer()
        
        pending_patterns = queryset.filter(status='pending_review')
        analyzer.approve_patterns_for_indexing([p.id for p in pending_patterns])
        
        count = pending_patterns.count()
        messages.success(request, f"Схвалено та індексовано {count} паттернів")
    approve_selected.short_description = "✅ Схвалити та індексувати обрані"
    
    def reject_selected(self, request, queryset):
        """Відхиляє обрані паттерни"""
        count = queryset.update(status='rejected')
        messages.success(request, f"Відхилено {count} паттернів")
    reject_selected.short_description = "❌ Відхилити обрані"
    
    def analyze_conversations(self, request, queryset):
        """Запускає аналіз діалогів"""
        analyzer = DialogAnalyzer()
        patterns_found = analyzer.analyze_recent_conversations(days=7)
        
        messages.success(request, f"Аналіз завершено! Знайдено {patterns_found} нових паттернів")
    analyze_conversations.short_description = "🔍 Аналізувати діалоги"


    class Media:
        js = ('admin/js/learning_admin.js',)