from django.contrib import admin
from .models import Product, ProductPricingPackage, ProductReview


class ProductPricingPackageInline(admin.TabularInline):
    """Inline для пакетів цін"""
    model = ProductPricingPackage
    extra = 1
    fields = [
        'name_en', 'name_uk', 'name_pl',
        'price', 'currency', 'billing_period',
        'is_recommended', 'has_trial', 'trial_days',
        'order', 'is_active'
    ]


class ProductReviewInline(admin.TabularInline):
    """Inline для відгуків"""
    model = ProductReview
    extra = 0
    fields = ['author_name', 'rating', 'is_featured', 'is_active']
    readonly_fields = ['date_created']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title_en',
        'slug',
        'priority',
        'is_featured',
        'is_active',
        'date_created'
    ]
    list_filter = ['is_active', 'is_featured', 'priority', 'date_created']
    search_fields = ['title_en', 'title_uk', 'title_pl', 'slug']
    prepopulated_fields = {'slug': ('title_en',)}

    filter_horizontal = ['related_services', 'tags']

    inlines = [ProductPricingPackageInline, ProductReviewInline]

    fieldsets = (
        ('📋 Основна інформація', {
            'fields': (
                'slug',
                'title_en', 'title_uk', 'title_pl',
                'is_active', 'is_featured', 'priority', 'order'
            )
        }),
        ('📝 Описи', {
            'fields': (
                'short_description_en', 'short_description_uk', 'short_description_pl',
                'description_en', 'description_uk', 'description_pl',
            )
        }),
        ('🎯 Для кого / Особливості', {
            'fields': (
                'target_audience_en', 'target_audience_uk', 'target_audience_pl',
                'features_en', 'features_uk', 'features_pl',
                'how_it_works_en', 'how_it_works_uk', 'how_it_works_pl',
            )
        }),
        ('📷 Медіа', {
            'fields': (
                'featured_image', 'og_image', 'icon',
                'gallery_image_1', 'gallery_image_2',
                'gallery_image_3', 'gallery_image_4',
                'video_url', 'video_file'
            )
        }),
        ('🔗 CTA та посилання', {
            'fields': (
                'cta_text_en', 'cta_text_uk', 'cta_text_pl',
                'cta_url'
            )
        }),
        ('🔍 SEO', {
            'fields': (
                'seo_title_en', 'seo_title_uk', 'seo_title_pl',
                'seo_description_en', 'seo_description_uk', 'seo_description_pl'
            )
        }),
        ('🏷️ Зв'язки', {
            'fields': ('related_services', 'tags')
        }),
        ('📅 Дати', {
            'fields': ('launch_date', 'date_created', 'date_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['date_created', 'date_updated']

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(ProductPricingPackage)
class ProductPricingPackageAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'name_en',
        'price',
        'currency',
        'billing_period',
        'is_recommended',
        'has_trial',
        'is_active'
    ]
    list_filter = ['product', 'currency', 'billing_period', 'is_recommended', 'has_trial', 'is_active']
    search_fields = ['name_en', 'name_uk', 'name_pl', 'product__title_en']

    fieldsets = (
        ('📦 Основна інформація', {
            'fields': (
                'product',
                'name_en', 'name_uk', 'name_pl',
                'order', 'is_active'
            )
        }),
        ('💰 Ціноутворення', {
            'fields': (
                'price', 'currency', 'billing_period',
                'is_recommended'
            )
        }),
        ('🎁 Trial', {
            'fields': (
                'has_trial', 'trial_days'
            )
        }),
        ('📝 Описи та можливості', {
            'fields': (
                'description_en', 'description_uk', 'description_pl',
                'features_en', 'features_uk', 'features_pl'
            )
        }),
    )


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'author_name',
        'author_company',
        'rating',
        'is_featured',
        'is_active',
        'date_created'
    ]
    list_filter = ['product', 'rating', 'is_featured', 'is_active', 'date_created']
    search_fields = ['author_name', 'author_company', 'product__title_en']

    fieldsets = (
        ('👤 Автор', {
            'fields': (
                'product',
                'author_name', 'author_position', 'author_company',
                'author_avatar'
            )
        }),
        ('⭐ Відгук', {
            'fields': (
                'rating',
                'review_text_en', 'review_text_uk', 'review_text_pl',
                'is_featured', 'is_active'
            )
        }),
        ('📅 Дата', {
            'fields': ('date_created',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['date_created']
