from django.contrib import admin
from django import forms
from django.utils.html import format_html
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import ServiceCategory, FAQ, ServiceFeature, ServiceOverview
from pricing.admin import ServicePricingInline

class SCForm(forms.ModelForm):
    description_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    description_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    description_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    target_audience_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    target_audience_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    target_audience_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    pricing_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    pricing_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    pricing_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    value_proposition_en = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    value_proposition_uk = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    value_proposition_pl = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    class Meta:
        model = ServiceCategory
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
    seo_description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = ServiceOverview
        fields = '__all__'

class ServiceFeatureAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceFeature
        fields = '__all__'


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    form = SCForm
    list_display = ("title_en","is_featured","priority","order","date_created", "pricing_count")
    list_editable = ("is_featured","priority","order")
    search_fields = ("title_en","title_uk","title_pl")
    prepopulated_fields = {"slug": ("title_en",)}
    filter_horizontal = ("tags",)
    
    inlines = [ServicePricingInline]
    
    def pricing_count(self, obj):
        count = obj.pricing_options.filter(is_active=True).count()
        if count == 0:
            return format_html('<span style="color: red;">⚠️ Немає цін</span>')
        return format_html('<span style="color: green;">💰 {} пакетів</span>', count)
    pricing_count.short_description = '💰 Ціни'
    
    fieldsets = (
        ("Basic", {"fields": ("title_en","title_uk","title_pl","slug","is_featured","priority","order","tags")}),
        ("Short Card Text", {"fields": ("short_description_en","short_description_uk","short_description_pl")}),
        ("Full Description", {"fields": ("description_en","description_uk","description_pl")}),
        ("For Whom", {"fields": ("target_audience_en","target_audience_uk","target_audience_pl")}),
        ("Business Value", {"fields": ("value_proposition_en","value_proposition_uk","value_proposition_pl")}),
        ("Media", {"fields": ("icon","main_image","video_url","video_file","gallery_image_1","gallery_image_2","gallery_image_3","gallery_image_4")}),
        ("SEO", {"fields": ("seo_title_en","seo_title_uk","seo_title_pl","seo_description_en","seo_description_uk","seo_description_pl")}),
    )




@admin.register(ServiceOverview)
class ServiceOverviewAdmin(admin.ModelAdmin):
    form = ServiceOverviewAdminForm
    list_display = ("title_en", "seo_title")
    search_fields = ("title_en", "title_uk", "title_pl")

@admin.register(ServiceFeature)
class ServiceFeatureAdmin(admin.ModelAdmin):
    form = ServiceFeatureAdminForm
    list_display = ("title_en", "icon", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title_en", "title_uk", "title_pl")

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    form = FAQAdminForm
    list_display = ("question_en", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("question_en", "question_uk", "question_pl")