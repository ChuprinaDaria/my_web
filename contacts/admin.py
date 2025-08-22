from django.contrib import admin
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
    list_display = ['name', 'email', 'subject', 'referred_from', 'is_processed', 'created_at']
    list_filter = ['is_processed', 'referred_from', 'created_at', 'company']
    search_fields = ['name', 'email', 'subject', 'company', 'message']
    readonly_fields = ['created_at', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Дані клієнта', {
            'fields': (
                ('name', 'email'),
                ('company', 'phone'),
                'subject',
                'message'
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
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
        self.message_user(request, f"Позначено {queryset.count()} заявок як оброблені")
    mark_as_processed.short_description = "Позначити як оброблені"
    
    def mark_as_unprocessed(self, request, queryset):
        queryset.update(is_processed=False)
        self.message_user(request, f"Позначено {queryset.count()} заявок як необроблені")
    mark_as_unprocessed.short_description = "Позначити як необроблені"