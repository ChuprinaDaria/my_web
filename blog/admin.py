from django.contrib import admin
from .models import BlogPost, BlogPostRating, BlogComment


class BlogPostRatingInline(admin.TabularInline):
    model = BlogPostRating
    extra = 0
    readonly_fields = ["score", "created_at", "ip_address", "user_agent"]


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title_en", "is_published", "published_at", "created_at"]
    list_filter = ["is_published", "created_at"]
    search_fields = ["title_en", "title_uk", "title_pl"]
    prepopulated_fields = {"slug": ("title_en",)}
    filter_horizontal = ["related_services"]
    inlines = [BlogPostRatingInline]
    fieldsets = (
        ("Status", {"fields": ("is_published", "published_at")}),
        ("Slug", {"fields": ("slug",)}),
        ("Titles", {"fields": ("title_uk", "title_pl", "title_en")}),
        ("Short descriptions", {"fields": ("short_description_uk", "short_description_pl", "short_description_en")}),
        ("Content", {"fields": ("content_uk", "content_pl", "content_en")}),
        ("SEO", {"fields": ("seo_title_uk", "seo_title_pl", "seo_title_en", "seo_description_uk", "seo_description_pl", "seo_description_en")}),
        ("Images", {"fields": ("main_image", "gallery_image_1", "gallery_image_2", "gallery_image_3", "gallery_image_4", "og_image")}),
        ("Relations", {"fields": ("related_services",)}),
    )


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ["post", "nickname", "created_at"]
    list_filter = ["created_at", "post"]
    search_fields = ["nickname", "text", "post__title_en", "post__title_uk", "post__title_pl"]
