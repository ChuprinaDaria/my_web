from django.contrib import admin
from django import forms
from django.utils.html import format_html
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import (
    Service,
    ServiceCategory,
    ServiceFeature,
    ServiceOverview,
    FAQ
)

# --- Форми з CKEditor ---
class ServiceAdminForm(forms.ModelForm):
    description_en = forms.CharField(widget=CKEditorUploadingWidget())
    description_uk = forms.CharField(widget=CKEditorUploadingWidget())
    description_pl = forms.CharField(widget=CKEditorUploadingWidget())
    
    short_description_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    short_description_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    short_description_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)

    # 🆕 ПОКРАЩЕННЯ для тегів
    tags = forms.ModelMultipleChoiceField(
        queryset=None,  # Встановимо в __init__
        widget=admin.widgets.FilteredSelectMultiple('Теги', False),
        required=False,
        help_text="Оберіть теги або створіть нові через /admin/core/tag/"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Завантажуємо активні теги
        try:
            from core.models import Tag
            self.fields['tags'].queryset = Tag.objects.filter(is_active=True).order_by('name')
        except:
            # Якщо модель Tag не існує
            pass

    class Meta:
        model = Service
        fields = '__all__'

class FAQAdminForm(forms.ModelForm):
    answer_en = forms.CharField(widget=CKEditorUploadingWidget())
    answer_uk = forms.CharField(widget=CKEditorUploadingWidget())
    answer_pl = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = FAQ
        fields = '__all__'

class ServiceOverviewAdminForm(forms.ModelForm):
    description_en = forms.CharField(widget=CKEditorUploadingWidget())
    description_uk = forms.CharField(widget=CKEditorUploadingWidget())
    description_pl = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = ServiceOverview
        fields = '__all__'

# --- Реєстрація моделей ---

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    form = ServiceAdminForm
    
    # 🏷️ ОНОВЛЕНИЙ список відображення з НОВИМИ ТЕГАМИ
    list_display = (
        "title_en", 
        "category", 
        "get_tags_display",      # 🆕 НОВІ ТЕГИ
        "get_priority_display",  # 🆕 ПРІОРИТЕТ
        "is_featured", 
        "is_active",
        "get_cross_stats",       # 🆕 СТАТИСТИКА КРОС-ПРОМОЦІЇ
        "date_created"
    )
    
    list_editable = ("is_featured", "is_active")
    
    # 🔍 ОНОВЛЕНІ фільтри з НОВИМИ ТЕГАМИ
    list_filter = (
        "tags",                  # 🆕 ФІЛЬТР ПО НОВИМ ТЕГАМ
        "category", 
        "priority",              # 🆕 ФІЛЬТР ПО ПРІОРИТЕТУ
        "is_featured",
        "is_active",
        "date_created"
    )
    
    # 🔍 ОНОВЛЕНИЙ пошук
    search_fields = (
        "title_en", "title_uk", "title_pl",
        "tags__name_en", "tags__name_uk", "tags__name_pl",  # 🆕 ПОШУК ПО ТЕГАМ
        "description_en", "description_uk", "description_pl"
    )
    
    prepopulated_fields = {"slug": ("title_en",)}
    
    # 🏷️ ОНОВЛЕНА структура полів з НОВОЮ СИСТЕМОЮ ТЕГІВ
    fieldsets = (
        ("📝 Basic Information", {
            "fields": ("title_en", "title_uk", "title_pl", "slug", "category", "icon")
        }),
        
        ("🏷️ НОВА СИСТЕМА ТЕГІВ - Крос-промоція", {
            "fields": ("tags",),
            "classes": ("wide",),
            "description": "🎯 Оберіть внутрішні теги для автоматичної крос-видачі з новинами та проєктами!"
        }),
        
        ("📊 Пріоритет та відображення", {
            "fields": (
                ("priority", "is_featured"),
                "order"
            ),
            "classes": ("wide",),
            "description": "Налаштування пріоритету та порядку відображення сервісу"
        }),
        
        ("📄 Service Content", {
            "fields": (
                ("short_description_en", "short_description_uk", "short_description_pl"),
                ("description_en", "description_uk", "description_pl"),
            ),
            "classes": ("collapse",)
        }),
        
        ("🔍 SEO", {
            "fields": (
                ("seo_title_en", "seo_title_uk", "seo_title_pl"),
                ("seo_description_en", "seo_description_uk", "seo_description_pl")
            ),
            "classes": ("collapse",)
        }),
        
        ("⚙️ Status", {
            "fields": ("is_active",),
            "classes": ("wide",)
        }),
    )
    
    # 🆕 НОВІ методи відображення
    def get_tags_display(self, obj):
        """🏷️ Показує НОВІ внутрішні теги з кольорами"""
        tags = obj.tags.filter(is_active=True)
        if not tags.exists():
            return format_html('<span style="color: #6c757d;">⚪ Немає тегів</span>')
        
        tag_html = []
        for tag in tags[:3]:  # Показуємо максимум 3 теги
            tag_html.append(format_html(
                '<span style="background: {}; color: white; padding: 2px 6px; '
                'border-radius: 8px; font-size: 11px; margin-right: 4px;">'
                '{} {}</span>',
                tag.color, tag.emoji, tag.get_name('uk')
            ))
        
        if tags.count() > 3:
            tag_html.append(format_html('<span style="color: #6c757d;">+{}</span>', tags.count() - 3))
        
        return format_html(''.join(tag_html))
    get_tags_display.short_description = "🏷️ Внутрішні теги"
    
    def get_priority_display(self, obj):
        """📊 Показує пріоритет з емодзі"""
        emoji = obj.get_priority_emoji()
        priority_colors = {
            1: '#6c757d',  # Сірий
            2: '#007bff',  # Синій
            3: '#ffc107',  # Жовтий
            4: '#fd7e14',  # Помаранчевий
            5: '#dc3545',  # Червоний
        }
        color = priority_colors.get(obj.priority, '#007bff')
        
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{} {}</span>',
            color, emoji, obj.get_priority_display().title()
        )
    get_priority_display.short_description = "📊 Пріоритет"
    
    def get_cross_stats(self, obj):
        """🔗 Показує статистику крос-промоції"""
        articles_count = obj.get_related_articles().count()
        projects_count = obj.get_related_projects().count()
        
        if articles_count == 0 and projects_count == 0:
            return format_html('<span style="color: #6c757d;">—</span>')
        
        stats_html = []
        if articles_count > 0:
            stats_html.append(format_html(
                '<span style="color: #007bff;">📰{}</span>', articles_count
            ))
        if projects_count > 0:
            stats_html.append(format_html(
                '<span style="color: #28a745;">🚀{}</span>', projects_count
            ))
        
        return format_html(' | '.join(stats_html))
    get_cross_stats.short_description = "🔗 Крос-промоція"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category').prefetch_related('tags')
    
    # 🎯 НОВІ дії в адмінці
    actions = [
        'mark_as_featured', 
        'set_high_priority',
        'auto_assign_tags_from_content',  # 🆕 НОВА ДІЯ
        'show_cross_promotion_stats'      # 🆕 НОВА ДІЯ
    ]
    
    def mark_as_featured(self, request, queryset):
        """✨ Позначити як рекомендовані"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'✨ {updated} сервісів позначено як рекомендовані.')
    mark_as_featured.short_description = "✨ Позначити як рекомендовані"
    
    def set_high_priority(self, request, queryset):
        """🔥 Встановити високий пріоритет"""
        updated = queryset.update(priority=4)
        self.message_user(request, f'🔥 {updated} сервісів отримали високий пріоритет.')
    set_high_priority.short_description = "🔥 Встановити високий пріоритет"
    
    # 🆕 НОВІ дії для роботи з тегами
    def auto_assign_tags_from_content(self, request, queryset):
        """🤖 Автоматично призначити теги на основі контенту"""
        updated_count = 0
        for service in queryset:
            assigned_tags = service.auto_assign_tags_from_content()
            if assigned_tags:
                updated_count += 1
        
        self.message_user(
            request, 
            f"🏷️ Автоматично призначено теги для {updated_count} сервісів"
        )
    auto_assign_tags_from_content.short_description = "🤖 Автопризначення тегів з контенту"
    
    def show_cross_promotion_stats(self, request, queryset):
        """📊 Показати статистику крос-промоції"""
        stats = []
        for service in queryset:
            related_articles = service.get_related_articles()
            related_projects = service.get_related_projects()
            tags_count = service.tags.count()
            
            stats.append(f"'{service.title_en}': {tags_count} тегів, "
                        f"{related_articles.count()} новин, "
                        f"{related_projects.count()} проєктів")
        
        stats_text = "<br>".join(stats[:10])  # Показуємо перші 10
        
        self.message_user(
            request,
            format_html(f"📊 Статистика крос-промоції:<br>{stats_text}"),
        )
    show_cross_promotion_stats.short_description = "📊 Показати статистику крос-промоції"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "tags":
            kwargs["help_text"] = format_html(
                '🏷️ Оберіть теги або <a href="/admin/core/tag/add/" target="_blank" '
                'style="background: #007bff; color: white; padding: 4px 8px; '
                'border-radius: 4px; text-decoration: none;">+ Створити новий тег</a>'
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("slug", "title_en", "services_count", "projects_count")
    prepopulated_fields = {"slug": ("title_en",)}
    
    def services_count(self, obj):
        return format_html(
            '<span style="color: #007bff; font-weight: bold;">🔧 {}</span>', 
            obj.services.count()
        )
    services_count.short_description = "Services"
    
    def projects_count(self, obj):
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">🚀 {}</span>', 
            obj.projects.count()
        )
    projects_count.short_description = "Projects"


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    form = FAQAdminForm
    list_display = ("question_en", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("question_en", "question_uk", "question_pl")
    list_filter = ("is_active",)
    
    fieldsets = (
        ("📝 Question", {
            "fields": ("question_en", "question_uk", "question_pl")
        }),
        ("💬 Answer", {
            "fields": ("answer_en", "answer_uk", "answer_pl")
        }),
        ("⚙️ Settings", {
            "fields": ("order", "is_active")
        }),
    )


@admin.register(ServiceFeature)
class ServiceFeatureAdmin(admin.ModelAdmin):
    list_display = ("get_icon_display", "title_en", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title_en", "title_uk", "title_pl")
    list_filter = ("is_active",)
    
    fieldsets = (
        ("🎨 Visual", {
            "fields": ("icon", "order")
        }),
        ("📝 Content", {
            "fields": ("title_en", "title_uk", "title_pl")
        }),
        ("⚙️ Status", {
            "fields": ("is_active",)
        }),
    )
    
    def get_icon_display(self, obj):
        """Показує іконку з назвою"""
        return format_html(
            '<span style="font-family: monospace; background: #f8f9fa; '
            'padding: 2px 6px; border-radius: 4px;">{}</span>',
            obj.icon or '—'
        )
    get_icon_display.short_description = "🎨 Icon"


@admin.register(ServiceOverview)
class ServiceOverviewAdmin(admin.ModelAdmin):
    form = ServiceOverviewAdminForm
    list_display = ("title_en", "seo_title", "has_og_image")
    
    fieldsets = (
        ("📝 Content", {
            "fields": ("title_en", "title_uk", "title_pl")
        }),
        ("📄 Description", {
            "fields": ("description_en", "description_uk", "description_pl"),
            "classes": ("collapse",)
        }),
        ("🔍 SEO", {
            "fields": ("seo_title", "seo_description", "og_image"),
            "classes": ("collapse",)
        }),
    )
    
    def has_og_image(self, obj):
        """Показує чи є OG зображення"""
        if obj.og_image:
            return format_html('<span style="color: #28a745;">✅ Є</span>')
        return format_html('<span style="color: #6c757d;">❌ Немає</span>')
    has_og_image.short_description = "🖼️ OG Image"