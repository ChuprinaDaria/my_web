from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import StaticPage

@admin.register(StaticPage)
class StaticPageAdmin(TranslatableAdmin):
    list_display = ('slug', 'get_title', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('slug', 'translations__title')
    
    fieldsets = (
        (None, {
            'fields': ('slug', 'is_active')
        }),
        ('Content', {
            'fields': ('title', 'content', 'meta_description')
        }),
    )
    
    def get_title(self, obj):
        return obj.safe_translation_getter('title', obj.slug)
    get_title.short_description = 'Title'