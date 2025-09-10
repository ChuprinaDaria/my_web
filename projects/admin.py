from django.contrib import admin
from django import forms
from django.utils.html import format_html
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import Project, ProjectReview, ProjectContactSubmission


# --- Форми з CKEditor ---
class ProjectAdminForm(forms.ModelForm):
    client_request_en = forms.CharField(widget=CKEditorUploadingWidget())
    client_request_uk = forms.CharField(widget=CKEditorUploadingWidget())
    client_request_pl = forms.CharField(widget=CKEditorUploadingWidget())
    
    implementation_en = forms.CharField(widget=CKEditorUploadingWidget())
    implementation_uk = forms.CharField(widget=CKEditorUploadingWidget())
    implementation_pl = forms.CharField(widget=CKEditorUploadingWidget())
    
    results_en = forms.CharField(widget=CKEditorUploadingWidget())
    results_uk = forms.CharField(widget=CKEditorUploadingWidget())
    results_pl = forms.CharField(widget=CKEditorUploadingWidget())
    
    short_description_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    short_description_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    short_description_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)

    client_request_extended_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    client_request_extended_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    client_request_extended_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    
    implementation_extended_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    implementation_extended_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    implementation_extended_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    
    results_extended_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    results_extended_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    results_extended_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    
    challenges_and_solutions_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    challenges_and_solutions_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    challenges_and_solutions_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    
    lessons_learned_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    lessons_learned_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    lessons_learned_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)

    class Meta:
        model = Project
        fields = '__all__'


class ProjectReviewAdminForm(forms.ModelForm):
    review_text_en = forms.CharField(widget=CKEditorUploadingWidget())
    review_text_uk = forms.CharField(widget=CKEditorUploadingWidget())
    review_text_pl = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = ProjectReview
        fields = '__all__'


# --- Inline для відгуків ---
class ProjectReviewInline(admin.StackedInline):
    model = ProjectReview
    form = ProjectReviewAdminForm
    extra = 0
    max_num = 1  # Один відгук на проєкт
    fieldsets = (
        ("Client Information", {
            "fields": ("client_name", "client_position", "client_company", "client_avatar", "rating")
        }),
        ("Review Text", {
            "fields": ("review_text_en", "review_text_uk", "review_text_pl")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
    )


# --- Реєстрація моделей ---

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    inlines = [ProjectReviewInline]
    
    # 🏷️ ОНОВЛЕНИЙ список відображення з НОВИМИ ТЕГАМИ
    list_display = (
        "title_en", 
        "category", 
        "get_tags_display",  # 🆕 НОВІ ТЕГИ
        "priority",
        "get_complexity_display", 
        "get_visual_badges_display",  # 🆕 переименовано для ясності
        "project_status",
        "is_featured", 
        "is_active", 
        "project_date", 
        "order"
    )
    
    list_editable = ("is_featured", "is_active", "order", "project_status", "priority")
    
    # 🔍 ОНОВЛЕНІ фільтри з НОВИМИ ТЕГАМИ
    list_filter = (
        "category",  # 🎯 КАТЕГОРІЯ - головний фільтр
        "priority",
        "complexity_level",
        "project_status",
        "is_featured", 
        "is_active", 
        "tags",  # 🏷️ ТЕГИ - нижчий пріоритет
        "is_top_project",
        "is_innovative",
        "is_ai_powered",
        "is_enterprise",
        "is_complex",
        "budget_range",
        "project_date"
    )
    
    # 🔍 ОНОВЛЕНИЙ пошук
    search_fields = (
        "title_en", "title_uk", "title_pl", 
        "technologies_used",
        "tags__name_en", "tags__name_uk", "tags__name_pl",  # 🆕 ПОШУК ПО ТЕГАМ
        "project_type_en", "project_type_uk", "project_type_pl",  # старі поля (deprecated)
        "custom_badge_en", "custom_badge_uk", "custom_badge_pl"
    )
    
    prepopulated_fields = {"slug": ("title_en",)}
    date_hierarchy = "project_date"
    
    # 🏷️ ОНОВЛЕНА структура полів з НОВОЮ СИСТЕМОЮ ТЕГІВ
    fieldsets = (
        ("📝 Basic Information", {
            "fields": ("title_en", "title_uk", "title_pl", "slug", "category")
        }),
        
        ("📊 Пріоритет та відображення", {
            "fields": (("priority", "is_featured"), "order")
        }),
        
        ("🏷️ Теги (опційно)", {
            "fields": ("tags",),
            "description": "🎯 Оберіть теги для підсилення крос-промоції"
        }),
        
        ("🎨 Візуальні бейджі (legacy)", {
            "fields": (
                # Спеціальні бейджі (в рядок)
                ("is_top_project", "is_innovative", "is_ai_powered"),
                ("is_enterprise", "is_complex"),
                
                # Кастомний бейдж
                ("custom_badge_en", "custom_badge_uk", "custom_badge_pl"),
                "custom_badge_color",
            ),
            "classes": ("collapse",),
            "description": "🎨 Старі візуальні бейджі для відображення. Рекомендовано використовувати нову систему тегів вище!"
        }),
        
        ("🗂️ DEPRECATED: Старі типи проєктів", {
            "fields": (
                ("project_type_en", "project_type_uk", "project_type_pl"),
            ),
            "classes": ("collapse",),
            "description": "⚠️ DEPRECATED: Ці поля застарілі. Використовуй нову систему тегів для кращої крос-промоції!"
        }),
        
        ("📊 Project Metrics & Status", {
            "fields": (
                ("complexity_level", "project_status"),
                ("budget_range", "development_duration_weeks"),
                "client_time_saved_hours",
            ),
            "classes": ("wide",),
            "description": "Метрики проєкту та його поточний статус"
        }),
        
        ("📄 Project Content", {
            "fields": (
                ("short_description_en", "short_description_uk", "short_description_pl"),
                ("client_request_en", "client_request_uk", "client_request_pl"),
                ("implementation_en", "implementation_uk", "implementation_pl"),
                ("results_en", "results_uk", "results_pl")
            ),
            "classes": ("collapse",)
        }),

        ("📄 Extended Project Content (Detail Page Only)", {
            "fields": (
                ("client_request_extended_en", "client_request_extended_uk", "client_request_extended_pl"),
                ("implementation_extended_en", "implementation_extended_uk", "implementation_extended_pl"),
                ("results_extended_en", "results_extended_uk", "results_extended_pl"),
                ("challenges_and_solutions_en", "challenges_and_solutions_uk", "challenges_and_solutions_pl"),
                ("lessons_learned_en", "lessons_learned_uk", "lessons_learned_pl")
            ),
            "classes": ("collapse",),
            "description": "Детальний контент тільки для сторінки проєкту (не показується на головній)"
        }),
        
        ("🖼️ Media Files", {
            "fields": (
                "featured_image",
                ("gallery_image_1", "gallery_image_2", "gallery_image_3"),
                ("video_url", "video_file")
            ),
            "classes": ("collapse",)
        }),
        
        ("💻 Technical Details", {
            "fields": (
                "technologies_used", 
                "project_url", 
                "project_date"
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
        
        ("⚙️ Status & Display", {
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
                tag.color, getattr(tag, 'icon', ''), tag.get_name('uk')
            ))
        
        if tags.count() > 3:
            tag_html.append(format_html('<span style="color: #6c757d;">+{}</span>', tags.count() - 3))
        
        return format_html(''.join(tag_html))
    get_tags_display.short_description = "🏷️ Внутрішні теги"
    
    def get_visual_badges_display(self, obj):
        """🎨 Показує СТАРІ візуальні бейджі (legacy)"""
        badges = []
        if obj.is_top_project:
            badges.append("👑TOP")
        if obj.is_innovative:
            badges.append("⚡INNO")
        if obj.is_ai_powered:
            badges.append("🤖AI")
        if obj.is_enterprise:
            badges.append("🏭ENT")
        if obj.is_complex:
            badges.append("🧩COMPLEX")
        if obj.custom_badge_uk:
            badges.append(f"✨{obj.custom_badge_uk[:8]}")
        
        if badges:
            return format_html(
                '<span style="color: #6c757d; font-size: 11px;">{}</span>',
                " | ".join(badges)
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    get_visual_badges_display.short_description = "🎨 Візуальні бейджі"
    
    def get_priority_display(self, obj):
        """Показує пріоритет з емодзі"""
        priority_icons = {
            1: "⚪ Низький",
            2: "🔵 Звичайний", 
            3: "🟡 Високий",
            4: "🟠 Критичний",
            5: "🔴 Топ проєкт"
        }
        return priority_icons.get(obj.priority, "🔵 Звичайний")
    get_priority_display.short_description = "Пріоритет"
    
    def get_complexity_display(self, obj):
        """Показує складність з зірочками"""
        stars = "⭐" * obj.complexity_level
        return f"{stars} ({obj.get_complexity_display_uk()})"
    get_complexity_display.short_description = "Складність"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category').prefetch_related('tags')
    
    # 🎯 ОНОВЛЕНІ дії в адмінці + НОВІ дії для тегів
    actions = [
        'mark_as_featured', 
        'mark_as_top', 
        'set_high_priority',
        'auto_assign_tags_from_legacy',  # 🆕 НОВА ДІЯ
        'show_cross_promotion_stats'     # 🆕 НОВА ДІЯ
    ]
    
    def mark_as_featured(self, request, queryset):
        """Позначити як рекомендовані"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} проєктів позначено як рекомендовані.')
    mark_as_featured.short_description = "✨ Позначити як рекомендовані"
    
    def mark_as_top(self, request, queryset):
        """Додати бейдж TOP"""
        updated = queryset.update(is_top_project=True)
        self.message_user(request, f'{updated} проєктів отримали бейдж TOP.')
    mark_as_top.short_description = "👑 Додати бейдж TOP"
    
    def set_high_priority(self, request, queryset):
        """Встановити високий пріоритет"""
        updated = queryset.update(priority=4)
        self.message_user(request, f'{updated} проєктів отримали високий пріоритет.')
    set_high_priority.short_description = "🔥 Встановити високий пріоритет"
    
    # 🆕 НОВІ дії для роботи з тегами
    def auto_assign_tags_from_legacy(self, request, queryset):
        """🤖 Автоматично призначити теги на основі старих полів"""
        updated_count = 0
        for project in queryset:
            assigned_tags = project.auto_assign_tags_from_legacy()
            if assigned_tags:
                updated_count += 1
        
        self.message_user(
            request, 
            f"🏷️ Автоматично призначено теги для {updated_count} проєктів"
        )
    auto_assign_tags_from_legacy.short_description = "🤖 Автопризначення тегів з legacy полів"
    
    def show_cross_promotion_stats(self, request, queryset):
        """📊 Показати статистику крос-промоції"""
        stats = []
        for project in queryset:
            related_articles = project.get_related_articles()
            related_services = project.get_related_services()
            tags_count = project.tags.count()
            
            stats.append(f"'{project.title_en}': {tags_count} тегів, "
                        f"{related_articles.count()} новин, "
                        f"{related_services.count()} сервісів")
        
        stats_text = "<br>".join(stats[:10])  # Показуємо перші 10
        
        self.message_user(
            request,
            format_html(f"📊 Статистика крос-промоції:<br>{stats_text}"),
        )
    show_cross_promotion_stats.short_description = "📊 Показати статистику крос-промоції"


@admin.register(ProjectReview) 
class ProjectReviewAdmin(admin.ModelAdmin):
    form = ProjectReviewAdminForm
    list_display = ("project", "client_name", "rating", "is_active")
    list_filter = ("rating", "is_active")
    search_fields = ("client_name", "client_company", "project__title_en")


@admin.register(ProjectContactSubmission)
class ProjectContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "project", "created_at", "is_processed")
    list_filter = ("is_processed", "created_at", "project")
    search_fields = ("name", "email", "company", "message")
    readonly_fields = ("created_at", "ip_address", "user_agent")
    list_editable = ("is_processed",)
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Contact Information", {
            "fields": ("project", "name", "email", "phone", "company")
        }),
        ("Message", {
            "fields": ("message",)
        }),
        ("Meta Data", {
            "fields": ("created_at", "ip_address", "user_agent"),
            "classes": ("collapse",)
        }),
        ("Admin", {
            "fields": ("is_processed", "admin_notes")
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project')