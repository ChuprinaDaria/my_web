from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'slug', 'name_uk', 'name_en']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('🏷️ Основна інформація', {
            'fields': ('name', 'slug')
        }),
        ('🌍 Багатомовність', {
            'fields': ('name_en', 'name_uk', 'name_pl'),
            'classes': ('collapse',)
        }),
        ('🎨 Дизайн', {
            'fields': ('icon', 'color', 'category')
        }),
        ('⚙️ Налаштування', {
            'fields': ('description', 'is_active', 'is_featured')
        })
    )