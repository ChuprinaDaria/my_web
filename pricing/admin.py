# pricing/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import PricingTier, ServicePricing, QuoteRequest


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name_uk', 'is_popular', 'order')
    list_editable = ('is_popular', 'order')
    list_filter = ('is_popular',)
    ordering = ['order']
    
    fieldsets = (
        ("Основна інформація", {
            'fields': ('name', 'is_popular', 'order')
        }),
        ("Назви (багатомовно)", {
            'fields': (
                'display_name_uk',
                'display_name_en', 
                'display_name_pl'
            )
        }),
        ("Описи (багатомовно)", {
            'fields': (
                'description_uk',
                'description_en',
                'description_pl'
            ),
            'classes': ('collapse',)
        })
    )


class ServicePricingInline(admin.TabularInline):
    """Inline для показу цін прямо в ServiceCategory"""
    model = ServicePricing
    fields = ('tier', 'price_from', 'price_to', 'timeline_weeks_from', 'complexity_level', 'is_active')
    extra = 0
    show_change_link = True


@admin.register(ServicePricing)
class ServicePricingAdmin(admin.ModelAdmin):
    list_display = (
        'service_category_link', 
        'tier_badge',
        'price_display', 
        'timeline_display',
        'complexity_badge',
        'is_active'
    )
    list_editable = ('is_active',)
    list_filter = (
        'service_category',
        'tier', 
        'complexity_level',
        'is_active'
    )
    search_fields = ('service_category__title_en', 'service_category__title_uk')
    ordering = ['service_category__title_en', 'tier__order']
    
    fieldsets = (
        ("🎯 Основна інформація", {
            'fields': (
                ('service_category', 'tier'),
                ('is_active', 'order', 'complexity_level')
            )
        }),
        ("💰 Ціна та час", {
            'fields': (
                ('price_from', 'price_to'),
                ('timeline_weeks_from', 'timeline_weeks_to')
            ),
            'description': "Залиш price_to та timeline_weeks_to пустими для фіксованої ціни/часу"
        }),
        ("✅ Що включено (українською)", {
            'fields': ('features_included_uk',),
            'description': "Кожна лінія = окрема фіча. Приклад:\n• Дизайн 5 сторінок\n• Адаптивна верстка\n• Базове SEO"
        }),
        ("✅ What's included (English)", {
            'fields': ('features_included_en',),
            'classes': ('collapse',)
        }),
        ("✅ Co jest włączone (Polish)", {
            'fields': ('features_included_pl',),
            'classes': ('collapse',)
        }),
        ("🎯 Для кого підходить", {
            'fields': (
                'suitable_for_uk',
                'suitable_for_en', 
                'suitable_for_pl'
            ),
            'classes': ('collapse',)
        })
    )
    
    def service_category_link(self, obj):
        """Посилання на категорію сервісу"""
        url = reverse('admin:services_servicecategory_change', args=[obj.service_category.pk])
        return format_html('<a href="{}">{}</a>', url, obj.service_category.title_en)
    service_category_link.short_description = '🗂️ Сервіс'
    service_category_link.admin_order_field = 'service_category__title_en'
    
    def tier_badge(self, obj):
        """Красивий бейдж для tier"""
        colors = {
            'basic': '#6c757d',      # сірий
            'standard': '#0d6efd',   # синій  
            'premium': '#198754',    # зелений
            'enterprise': '#dc3545'  # червоний
        }
        color = colors.get(obj.tier.name, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.tier.get_name_display()
        )
    tier_badge.short_description = '🏷️ Рівень'
    tier_badge.admin_order_field = 'tier__order'
    
    def price_display(self, obj):
        """Відформатована ціна"""
        return obj.get_price_display()
    price_display.short_description = '💰 Ціна'
    price_display.admin_order_field = 'price_from'
    
    def timeline_display(self, obj):
        """Відформатований час"""
        return obj.get_timeline_display() 
    timeline_display.short_description = '⏰ Час'
    timeline_display.admin_order_field = 'timeline_weeks_from'
    
    def complexity_badge(self, obj):
        """Бейдж складності"""
        colors = {
            'simple': '#28a745',   # зелений
            'medium': '#ffc107',   # жовтий
            'complex': '#fd7e14',  # помаранчевий  
            'enterprise': '#dc3545' # червоний
        }
        color = colors.get(obj.complexity_level, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">{}</span>',
            color, obj.get_complexity_level_display()
        )
    complexity_badge.short_description = '⚡ Складність'
    complexity_badge.admin_order_field = 'complexity_level'


@admin.register(QuoteRequest)  
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = (
        'client_name',
        'client_email', 
        'service_category',
        'status_badge',
        'date_created',
        'actions_column'
    )
    list_filter = (
        'status',
        'service_category',
        'wants_consultation', 
        'pdf_generated',
        'email_sent',
        'date_created'
    )
    search_fields = ('client_name', 'client_email', 'original_query')
    readonly_fields = ('date_created', 'date_updated', 'session_id', 'ip_address')
    ordering = ['-date_created']
    
    fieldsets = (
        ("👤 Клієнт", {
            'fields': (
                ('client_name', 'client_email'),
                ('client_phone', 'client_company')
            )
        }),
        ("💬 Запит", {
            'fields': (
                'original_query',
                'service_category',
                'ai_analysis'
            )
        }),
        ("💰 Прорахунок", {
            'fields': (
                'suggested_pricing',
                ('pdf_generated', 'pdf_file'),
                'email_sent'
            )
        }),
        ("📅 Консультація", {
            'fields': (
                'wants_consultation',
                'consultation_scheduled', 
                'google_event_id'
            )
        }),
        ("📊 Статус та метадані", {
            'fields': (
                'status',
                ('session_id', 'ip_address'),
                'user_agent',
                ('date_created', 'date_updated')
            ),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        """Кольоровий бейдж статусу"""
        colors = {
            'new': '#6c757d',        # сірий
            'analyzed': '#0d6efd',   # синій
            'quoted': '#198754',     # зелений
            'consulted': '#fd7e14',  # помаранчевий
            'converted': '#28a745',  # темно-зелений
            'closed': '#dc3545'      # червоний
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '📊 Статус'
    status_badge.admin_order_field = 'status'
    
    def actions_column(self, obj):
        """Швидкі дії"""
        actions = []
        
        if not obj.pdf_generated and obj.suggested_pricing:
            actions.append('<a href="#" onclick="generatePdf({})" style="color: #0d6efd;">📄 Генерувати PDF</a>'.format(obj.pk))
            
        if not obj.email_sent and obj.pdf_generated:
            actions.append('<a href="#" onclick="sendEmail({})" style="color: #198754;">📧 Відправити</a>'.format(obj.pk))
            
        if obj.wants_consultation and not obj.consultation_scheduled:
            actions.append('<a href="#" onclick="scheduleConsultation({})" style="color: #fd7e14;">📅 Записати</a>'.format(obj.pk))
        
        return mark_safe(' | '.join(actions)) if actions else '-'
    actions_column.short_description = '⚡ Дії'