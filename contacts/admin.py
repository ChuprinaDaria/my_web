from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
import csv
from .models import Contact, ContactSubmission

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'city', 'is_active']
    list_filter = ['is_active', 'city', 'country_en']
    search_fields = ['email', 'phone', 'address_line_1_en', 'address_line_1_uk']
    
    fieldsets = (
        ('Основна інформація', {
            'fields': (
                ('title_en', 'title_uk', 'title_pl'),
                ('description_en', 'description_uk', 'description_pl'),
                'is_active'
            )
        }),
        ('Контактні дані', {
            'fields': (
                ('email', 'phone'),
                'google_maps_url'
            )
        }),
        ('Фото', {
            'fields': (
                'hero_photo',  # Нове поле для Hero секції
                ('hero_title_en', 'hero_title_uk', 'hero_title_pl'),
                ('hero_description_en', 'hero_description_uk', 'hero_description_pl'),
                'office_photo'  # Існуюче для секції адреси
            ),
            'description': 'Hero photo - для головної секції, Office photo - для блоку адреси'
        }),
        ('Адреса', {
            'fields': (
                ('address_line_1_en', 'address_line_1_uk', 'address_line_1_pl'),
                # ВИДАЛЯЄМО address_line_2 та address_line_3
                ('city', 'postal_code'),
                ('country_en', 'country_uk', 'country_pl')
            )
        }),
        ('SEO', {
            'fields': (
                ('seo_title_en', 'seo_title_uk', 'seo_title_pl'),
                ('seo_description_en', 'seo_description_uk', 'seo_description_pl')
            ),
            'classes': ['collapse']
        })
    )

@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'subject', 'status', 'assigned_to', 
        'lead_score', 'estimated_budget', 'is_processed', 'created_at'
    ]
    list_filter = [
        'status', 'assigned_to', 'lead_source', 'is_processed', 
        'created_at', 'company'
    ]
    search_fields = ['name', 'email', 'subject', 'company', 'message']
    readonly_fields = ['created_at', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Дані клієнта', {
            'fields': (
                ('name', 'email'),
                ('phone', 'company'),
                'subject',
                'message'
            )
        }),
        ('CRM інформація', {
            'fields': (
                ('status', 'assigned_to'),
                ('lead_score', 'estimated_budget'),
                ('lead_source', 'expected_close_date'),
                ('last_contact_date', 'next_follow_up')
            )
        }),
        ('Мета дані', {
            'fields': (
                'referred_from',
                'created_at',
                'ip_address',
                'user_agent'
            ),
            'classes': ['collapse']
        }),
        ('Адміністрування', {
            'fields': (
                'is_processed',
                'admin_notes'
            )
        })
    )
    
    # Дозволяємо масове оновлення статусу
    list_editable = ['status', 'assigned_to', 'lead_score']  # Редагування прямо зі списку
    actions = ['mark_as_processed', 'mark_as_unprocessed', 'assign_to_manager', 'mark_as_qualified', 'export_to_csv']
    
    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
        self.message_user(request, f"Позначено {queryset.count()} заявок як оброблені")
    mark_as_processed.short_description = "Позначити як оброблені"
    
    def mark_as_unprocessed(self, request, queryset):
        queryset.update(is_processed=False)
        self.message_user(request, f"Позначено {queryset.count()} заявок як необроблені")
    mark_as_unprocessed.short_description = "Позначити як необроблені"
    
    def assign_to_manager(self, request, queryset):
        """Масове призначення менеджера"""
        from django.contrib.auth.models import User
        managers = User.objects.filter(groups__name__in=['CRM Users', 'CRM Managers', 'CRM Admins'])
        if managers.exists():
            # Простий спосіб - призначити першого менеджера
            manager = managers.first()
            queryset.update(assigned_to=manager)
            self.message_user(request, f"Призначено {queryset.count()} заявок менеджеру {manager.username}")
        else:
            self.message_user(request, "Немає доступних менеджерів CRM", level='ERROR')
    assign_to_manager.short_description = "Призначити менеджера"
    
    def mark_as_qualified(self, request, queryset):
        """Позначити як кваліфікований лід"""
        queryset.update(status='qualified')
        self.message_user(request, f"Позначено {queryset.count()} заявок як кваліфіковані")
    
    mark_as_qualified.short_description = "Позначити як кваліфіковані"
    
    def export_to_csv(self, request, queryset):
        """Експорт лідов в CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Ім\'я', 'Email', 'Телефон', 'Компанія', 'Тема', 
            'Статус', 'Призначено', 'Оцінка ліда', 'Бюджет', 
            'Джерело', 'Дата створення', 'IP адреса'
        ])
        
        for lead in queryset:
            writer.writerow([
                lead.id,
                lead.name,
                lead.email,
                lead.phone or '',
                lead.company or '',
                lead.subject,
                lead.get_status_display(),
                lead.assigned_to.username if lead.assigned_to else '',
                lead.lead_score,
                lead.estimated_budget or '',
                lead.get_lead_source_display(),
                lead.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                lead.ip_address or ''
            ])
        
        return response
    
    export_to_csv.short_description = "Експорт в CSV"