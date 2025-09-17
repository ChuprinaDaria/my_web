from django.contrib import admin
from django.utils.html import format_html
from .models import About, AboutImage

class AboutImageInline(admin.TabularInline):
    model = AboutImage
    extra = 3
    fields = ('image', 'alt_text_en', 'alt_text_uk', 'alt_text_pl', 'order', 'is_active')

@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    inlines = [AboutImageInline]
    
    list_display = ('title_en', 'is_active', 'has_video', 'has_gallery', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title_en', 'title_uk', 'title_pl')
    
    fieldsets = (
        ("🌍 Basic Info", {
            "fields": (
                ("title_en", "title_uk", "title_pl"),
                ("subtitle_en", "subtitle_uk", "subtitle_pl")
            )
        }),
        
        ("📝 Content", {
            "fields": (
                ("story_en", "story_uk", "story_pl"),
                ("services_en", "services_uk", "services_pl"), 
                ("mission_en", "mission_uk", "mission_pl")
            )
        }),
        
        ("🎥 Media", {
            "fields": (
                ("gallery_image_1", "gallery_image_2", "gallery_image_3"),
                ("video_url", "video_file")
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
            "fields": ("is_active",)
        }),
    )
    
    def has_video(self, obj):
        return bool(obj.video_url or obj.video_file)
    has_video.boolean = True
    has_video.short_description = "📹"
    
    def has_gallery(self, obj):
        return bool(obj.gallery_image_1 or obj.gallery_image_2 or obj.gallery_image_3)
    has_gallery.boolean = True
    has_gallery.short_description = "🖼️"