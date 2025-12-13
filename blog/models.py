from django.db import models
from django.urls import reverse
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.utils.translation import get_language, override


class BlogPost(models.Model):
    slug = models.SlugField(max_length=255, unique=True)

    title_en = models.CharField(max_length=255)
    title_uk = models.CharField(max_length=255)
    title_pl = models.CharField(max_length=255)

    short_description_en = RichTextField(blank=True, null=True)
    short_description_uk = RichTextField(blank=True, null=True)
    short_description_pl = RichTextField(blank=True, null=True)

    content_en = RichTextField()
    content_uk = RichTextField()
    content_pl = RichTextField()

    seo_title_en = models.CharField(max_length=255, blank=True, null=True)
    seo_title_uk = models.CharField(max_length=255, blank=True, null=True)
    seo_title_pl = models.CharField(max_length=255, blank=True, null=True)

    seo_description_en = models.TextField(blank=True, null=True)
    seo_description_uk = models.TextField(blank=True, null=True)
    seo_description_pl = models.TextField(blank=True, null=True)

    main_image = models.ImageField(upload_to="blog/main/", blank=True, null=True)
    gallery_image_1 = models.ImageField(upload_to="blog/gallery/", blank=True, null=True)
    gallery_image_2 = models.ImageField(upload_to="blog/gallery/", blank=True, null=True)
    gallery_image_3 = models.ImageField(upload_to="blog/gallery/", blank=True, null=True)
    gallery_image_4 = models.ImageField(upload_to="blog/gallery/", blank=True, null=True)

    og_image = models.ImageField(upload_to="blog/og/", blank=True, null=True)

    related_services = models.ManyToManyField(
        "services.ServiceCategory",
        blank=True,
        related_name="blog_posts",
    )

    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Blog post"
        verbose_name_plural = "Blog posts"

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_en or self.title_uk)
        super().save(*args, **kwargs)

    def get_title(self, lang=None):
        lang = (lang or get_language() or "en").lower()
        return getattr(self, f"title_{lang}", self.title_en)

    def get_short(self, lang=None):
        lang = (lang or get_language() or "en").lower()
        return getattr(self, f"short_description_{lang}", None)

    def get_content(self, lang=None):
        lang = (lang or get_language() or "en").lower()
        return getattr(self, f"content_{lang}", None)

    def get_seo_title(self, lang=None):
        lang = (lang or get_language() or "en").lower()
        value = getattr(self, f"seo_title_{lang}", None)
        return value or self.get_title(lang)

    def get_seo_description(self, lang=None):
        lang = (lang or get_language() or "en").lower()
        value = getattr(self, f"seo_description_{lang}", None)
        if value:
            return value
        short = self.get_short(lang)
        return short or ""

    def get_gallery_images(self):
        images = []
        if self.gallery_image_1:
            images.append(self.gallery_image_1)
        if self.gallery_image_2:
            images.append(self.gallery_image_2)
        if self.gallery_image_3:
            images.append(self.gallery_image_3)
        if self.gallery_image_4:
            images.append(self.gallery_image_4)
        return images

    def get_average_rating(self):
        agg = self.ratings.aggregate(
            avg=models.Avg("score"),
            count=models.Count("id"),
        )
        return agg.get("avg") or 0, agg.get("count") or 0

    def get_absolute_url(self, language: str = None):
        """URL поста блогу з підтримкою мов. Англійська без /en/, uk/pl з префіксом."""
        lang = (language or get_language() or 'en').lower()
        with override(lang):
            return reverse('blog:blog_detail', kwargs={'slug': self.slug})


class BlogPostRating(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="ratings")
    score = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Blog post rating"
        verbose_name_plural = "Blog post ratings"


class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="comments")
    nickname = models.CharField(max_length=80)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Blog comment"
        verbose_name_plural = "Blog comments"

