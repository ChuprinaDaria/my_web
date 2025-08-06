from django.contrib import admin
from django import forms
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


# --- Реєстрація моделей (ТІЛЬКИ ОДИН РАЗ КОЖНА) ---

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    inlines = [ProjectReviewInline]
    
    list_display = ("title_en", "category", "is_featured", "is_active", "project_date", "order")
    list_editable = ("is_featured", "is_active", "order")
    list_filter = ("category", "is_featured", "is_active", "project_date")
    search_fields = ("title_en", "title_uk", "title_pl", "technologies_used")
    prepopulated_fields = {"slug": ("title_en",)}
    date_hierarchy = "project_date"
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("title_en", "title_uk", "title_pl", "slug", "category")
        }),
        ("Project Content", {
            "fields": (
                "short_description_en", "short_description_uk", "short_description_pl",
                "client_request_en", "client_request_uk", "client_request_pl",
                "implementation_en", "implementation_uk", "implementation_pl",
                "results_en", "results_uk", "results_pl"
            )
        }),
        ("Media Files", {
            "fields": (
                "featured_image",
                "gallery_image_1", "gallery_image_2", "gallery_image_3",
                "video_url", "video_file"
            ),
            "classes": ("collapse",)
        }),
        ("Project Details", {
            "fields": ("technologies_used", "project_url", "project_date")
        }),
        ("SEO", {
            "fields": (
                "seo_title_en", "seo_title_uk", "seo_title_pl",
                "seo_description_en", "seo_description_uk", "seo_description_pl"
            ),
            "classes": ("collapse",)
        }),
        ("Status & Display", {
            "fields": ("is_active", "is_featured", "order")
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


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