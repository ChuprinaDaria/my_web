from django.contrib import admin
from django import forms
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
    list_display = ("title_en", "category", "date_created")
    prepopulated_fields = {"slug": ("title_en",)}
    search_fields = ("title_en", "title_uk", "title_pl")
    list_filter = ("category", "is_active")
    fieldsets = (
        (None, {
            "fields": ("title_en", "title_uk", "title_pl", "slug",
                       "short_description_en", "short_description_uk", "short_description_pl",
                       "description_en", "description_uk", "description_pl",
                       "icon", "category", "is_active")
        }),
        ("SEO", {
            "fields": ("seo_title_en", "seo_title_uk", "seo_title_pl",
                       "seo_description_en", "seo_description_uk", "seo_description_pl")
        }),
    )




@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("slug", "title_en", "services_count", "projects_count")
    prepopulated_fields = {"slug": ("title_en",)}
    
    def services_count(self, obj):
        return obj.services.count()
    services_count.short_description = "Services"
    
    def projects_count(self, obj):
        return obj.projects.count()
    projects_count.short_description = "Projects"

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    form = FAQAdminForm
    list_display = ("question_en", "order")
    list_editable = ("order",)
    search_fields = ("question_en", "question_uk", "question_pl")


@admin.register(ServiceFeature)
class ServiceFeatureAdmin(admin.ModelAdmin):
    list_display = ("icon", "title_en", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title_en", "title_uk", "title_pl")


@admin.register(ServiceOverview)
class ServiceOverviewAdmin(admin.ModelAdmin):
    form = ServiceOverviewAdminForm
    list_display = ("title_en", "seo_title")