from django.db import models
from django import forms 
from ckeditor.fields import RichTextField
from services.models import ServiceCategory
from django.utils.text import slugify  


class Project(models.Model):
    slug = models.SlugField(max_length=255, unique=True)
    
    # Зв'язок з категорією сервісів
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='projects',
        null=True,
        blank=True,
        help_text="Категорія сервісу, до якої належить проєкт"
    )
    
    # Заголовки проєкту (багатомовність)
    title_en = models.CharField(max_length=255)
    title_uk = models.CharField(max_length=255)
    title_pl = models.CharField(max_length=255)
    
    # Короткий опис для карток
    short_description_en = RichTextField(blank=True, null=True, help_text="Короткий опис для відображення в картках")
    short_description_uk = RichTextField(blank=True, null=True)
    short_description_pl = RichTextField(blank=True, null=True)
    
    # Запит клієнта
    client_request_en = RichTextField(help_text="Що хотів клієнт, яка була задача")
    client_request_uk = RichTextField()
    client_request_pl = RichTextField()
    
    # Реалізація - що було зроблено
    implementation_en = RichTextField(help_text="Як було реалізовано, які технології використали")
    implementation_uk = RichTextField()
    implementation_pl = RichTextField()
    
    # Результат - що принесло клієнту  
    results_en = RichTextField(help_text="Яких результатів досяг клієнт, економія часу/грошей")
    results_uk = RichTextField()
    results_pl = RichTextField()
    
    # Медіа файли для проєкту
    featured_image = models.ImageField(
        upload_to="projects/images/", 
        blank=True, 
        null=True,
        help_text="Основне зображення проєкту"
    )
    
    gallery_image_1 = models.ImageField(upload_to="projects/gallery/", blank=True, null=True)
    gallery_image_2 = models.ImageField(upload_to="projects/gallery/", blank=True, null=True)
    gallery_image_3 = models.ImageField(upload_to="projects/gallery/", blank=True, null=True)
    
    # Відео (може бути YouTube URL або завантажений файл)
    video_url = models.URLField(blank=True, null=True, help_text="YouTube, Vimeo або інший URL")
    video_file = models.FileField(upload_to="projects/videos/", blank=True, null=True, help_text="Або завантажте відео файл")
    
    # Технології що використовувались
    technologies_used = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Список технологій через кому: Python, Django, React, OpenAI"
    )
    
    # Посилання на проєкт (якщо публічний)
    project_url = models.URLField(blank=True, null=True, help_text="Посилання на готовий проєкт")
    
    # SEO поля
    seo_title_en = models.CharField(max_length=255)
    seo_title_uk = models.CharField(max_length=255, blank=True, null=True)
    seo_title_pl = models.CharField(max_length=255, blank=True, null=True)
    
    seo_description_en = models.TextField(max_length=300)
    seo_description_uk = models.TextField(max_length=300, blank=True, null=True)
    seo_description_pl = models.TextField(max_length=300, blank=True, null=True)
    
    # Статус та порядок
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Показувати на головній сторінці")
    order = models.PositiveIntegerField(default=0, help_text="Порядок відображення")
    
    # Дати
    project_date = models.DateField(help_text="Коли був виконаний проєкт")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_en)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['-order', '-project_date']
    
    def __str__(self):
        return self.title_en
    
    def get_technologies_list(self):
        """Повертає список технологій як масив"""
        if self.technologies_used:
            return [tech.strip() for tech in self.technologies_used.split(',')]
        return []


class ProjectReview(models.Model):
    """Відгуки клієнтів про проєкти"""
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='review'
    )
    
    # Інформація про клієнта
    client_name = models.CharField(max_length=255, help_text="Ім'я клієнта (може бути псевдонім)")
    client_position = models.CharField(max_length=255, blank=True, null=True, help_text="Посада в компанії")
    client_company = models.CharField(max_length=255, blank=True, null=True, help_text="Назва компанії")
    client_avatar = models.ImageField(upload_to="projects/reviews/", blank=True, null=True)
    
    # Відгук (багатомовний)
    review_text_en = RichTextField()
    review_text_uk = RichTextField()
    review_text_pl = RichTextField()
    
    # Рейтинг
    rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        default=5,
        help_text="Рейтинг від 1 до 5 зірок"
    )
    
    # Статус
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Project Review"
        verbose_name_plural = "Project Reviews"
    
    def __str__(self):
        return f"Review for {self.project.title_en} by {self.client_name}"


class ProjectContactSubmission(models.Model):
    """Форма зворотного зв'язку на сторінці проєкту"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='contact_submissions'
    )
    
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    
    # Мета дані
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Статус обробки
    is_processed = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Project Contact Submission"
        verbose_name_plural = "Project Contact Submissions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Contact from {self.name} for {self.project.title_en}"