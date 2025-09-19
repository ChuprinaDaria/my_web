from django.db import models
from parler.models import TranslatableModel, TranslatedFields
from ckeditor.fields import RichTextField

class StaticPage(TranslatableModel):
    slug = models.SlugField(
        max_length=100, 
        unique=True,
        help_text="URL slug (privacy-policy, terms-of-service, cookies-policy)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    translations = TranslatedFields(
        title=models.CharField(max_length=200),
        content=RichTextField(),
        meta_description=models.TextField(
            max_length=160, 
            blank=True,
            help_text="SEO meta description (до 160 символів)"
        )
    )
    
    class Meta:
        verbose_name = "Static Page"
        verbose_name_plural = "Static Pages"
        
    def __str__(self):
        return f"{self.slug} ({self.safe_translation_getter('title', self.slug)})"