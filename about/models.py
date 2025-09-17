from django.db import models
from ckeditor.fields import RichTextField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class About(models.Model):
    # Основна інформація
    title_en = models.CharField(max_length=255, default="About Lazysoft")
    title_uk = models.CharField(max_length=255, default="Про Lazysoft")  
    title_pl = models.CharField(max_length=255, default="O Lazysoft")
    
    subtitle_en = models.CharField(max_length=500, blank=True)
    subtitle_uk = models.CharField(max_length=500, blank=True)
    subtitle_pl = models.CharField(max_length=500, blank=True)
    
    # Контент секції
    story_en = RichTextField()
    story_uk = RichTextField()
    story_pl = RichTextField()
    
    services_en = RichTextField()
    services_uk = RichTextField() 
    services_pl = RichTextField()
    
    mission_en = RichTextField()
    mission_uk = RichTextField()
    mission_pl = RichTextField()
    
    # SEO поля
    seo_title_en = models.CharField(max_length=255, blank=True)
    seo_title_uk = models.CharField(max_length=255, blank=True)
    seo_title_pl = models.CharField(max_length=255, blank=True)
    
    seo_description_en = models.TextField(max_length=300, blank=True)
    seo_description_uk = models.TextField(max_length=300, blank=True)
    seo_description_pl = models.TextField(max_length=300, blank=True)
    
    # Медіа файли (як в project)
    gallery_image_1 = models.ImageField(upload_to="about/gallery/", blank=True, null=True)
    gallery_image_2 = models.ImageField(upload_to="about/gallery/", blank=True, null=True) 
    gallery_image_3 = models.ImageField(upload_to="about/gallery/", blank=True, null=True)
    
    # Відео
    video_url = models.URLField(blank=True, null=True, help_text=_("YouTube, Vimeo або інший URL"))
    video_file = models.FileField(upload_to="about/videos/", blank=True, null=True, help_text=_("Або завантажте відео файл"))
    
    # Контроль
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("About Page")
        verbose_name_plural = _("About Pages")
        
    def __str__(self):
        return f"About Page - {self.title_en}"

class AboutImage(models.Model):
    about = models.ForeignKey(About, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="about/images/")
    
    alt_text_en = models.CharField(max_length=255, blank=True)
    alt_text_uk = models.CharField(max_length=255, blank=True) 
    alt_text_pl = models.CharField(max_length=255, blank=True)
    
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = _("About Image")
        verbose_name_plural = _("About Images")
        
    def __str__(self):
        return f"Image for {self.about.title_en}"