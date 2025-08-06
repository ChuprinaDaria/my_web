from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify


class ServiceCategory(models.Model):
    slug = models.SlugField(unique=True)

    title_en = models.CharField(max_length=255)
    title_uk = models.CharField(max_length=255)
    title_pl = models.CharField(max_length=255)

    description_en = RichTextField(blank=True, null=True)
    description_uk = RichTextField(blank=True, null=True)
    description_pl = RichTextField(blank=True, null=True)

    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ['title_en']

    def __str__(self):
        return self.title_en


class Service(models.Model):
    slug = models.SlugField(max_length=255, unique=True)

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='services',
        null=True,
        blank=True
    )

    title_en = models.CharField(max_length=255)
    title_uk = models.CharField(max_length=255)
    title_pl = models.CharField(max_length=255)

    short_description_en = RichTextField(blank=True, null=True)
    short_description_uk = RichTextField(blank=True, null=True)
    short_description_pl = RichTextField(blank=True, null=True)

    description_en = RichTextField()
    description_uk = RichTextField()
    description_pl = RichTextField()

    icon = models.ImageField(upload_to="services/icons/", blank=True, null=True)

    seo_title_en = models.CharField(max_length=255)
    seo_title_uk = models.CharField(max_length=255, blank=True, null=True)
    seo_title_pl = models.CharField(max_length=255, blank=True, null=True)

    seo_description_en = RichTextField(default="To be added")
    seo_description_uk = RichTextField(blank=True, null=True)
    seo_description_pl = RichTextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_uk)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['-date_created']

    def __str__(self):
        return self.title_en


class FAQ(models.Model):
    question_en = models.CharField(max_length=255)
    answer_en = RichTextField()
    question_uk = models.CharField(max_length=255)
    answer_uk = RichTextField()
    question_pl = models.CharField(max_length=255)
    answer_pl = RichTextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question_en


class ServiceOverview(models.Model):
    title_en = models.CharField(max_length=255)
    title_uk = models.CharField(max_length=255)
    title_pl = models.CharField(max_length=255)
    description_en = RichTextField()
    description_uk = RichTextField()
    description_pl = RichTextField()
    seo_title = models.CharField(max_length=255)
    seo_description = RichTextField()
    og_image = models.ImageField(upload_to='services/og/', null=True, blank=True)


class ServiceFeature(models.Model):
    icon = models.CharField(max_length=50, help_text="Назва SVG-іконки (ID з use #id)")
    order = models.PositiveIntegerField(default=0)

    title_en = models.CharField(max_length=255)
    title_uk = models.CharField(max_length=255)
    title_pl = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Service Feature"
        verbose_name_plural = "Service Features"

    def __str__(self):
        return self.title_en