# core/models.py
from django.db import models
from django.utils.text import slugify

class Tag(models.Model):
    """Універсальні теги для всіх сутностей: новини, проєкти, сервіси"""
    
    # Основні поля
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    
    # Багатомовність
    name_en = models.CharField(max_length=50, blank=True, help_text="English name")
    name_uk = models.CharField(max_length=50, blank=True, help_text="Українська назва") 
    name_pl = models.CharField(max_length=50, blank=True, help_text="Polska nazwa")
    
    # Візуальні налаштування
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text="Hex color для відображення тегу"
    )
    icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text="CSS class або emoji для іконки"
    )
    
    # Категоризація тегів
    TAG_CATEGORY_CHOICES = [
        ('technology', '💻 Technology'),
        ('industry', '🏭 Industry'), 
        ('service', '🔧 Service Type'),
        ('ai', '🤖 AI & ML'),
        ('business', '💼 Business'),
        ('development', '⚡ Development'),
    ]
    category = models.CharField(
        max_length=20,
        choices=TAG_CATEGORY_CHOICES,
        default='technology',
        help_text="Категорія тегу для групування"
    )
    
    # Метадані
    description = models.TextField(blank=True, help_text="Опис тегу")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Показувати в топі")
    
    # Статистика використання  
    usage_count = models.PositiveIntegerField(default=0, help_text="Скільки разів використовується")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['-is_featured', '-usage_count', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_name(self, language='uk'):
        """Повертає назву тегу для конкретної мови"""
        name_field = f'name_{language}'
        return getattr(self, name_field, '') or self.name
    
    def update_usage_count(self):
        """Оновлює лічильник використання"""
        from news.models import ProcessedArticle
        from projects.models import Project  
        from services.models import Service
        
        count = (
            self.articles.count() + 
            self.projects.count() + 
            self.services.count()
        )
        self.usage_count = count
        self.save(update_fields=['usage_count'])
    
    @classmethod
    def get_popular_tags(cls, limit=10):
        """Повертає популярні теги"""
        return cls.objects.filter(
            is_active=True,
            usage_count__gt=0
        ).order_by('-usage_count')[:limit]
    
    @classmethod 
    def get_by_category(cls, category):
        """Повертає теги по категорії"""
        return cls.objects.filter(
            category=category,
            is_active=True
        ).order_by('-usage_count')