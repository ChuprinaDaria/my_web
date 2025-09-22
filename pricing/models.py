# pricing/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from services.models import ServiceCategory


class PricingTier(models.Model):
    """Рівні цін - базовий, стандарт, преміум"""
    
    TIER_CHOICES = [
        ('basic', '🥉 Базовий'),
        ('standard', '🥈 Стандарт'), 
        ('premium', '🥇 Преміум'),
        ('enterprise', '💎 Корпоративний'),
    ]
    
    name = models.CharField(max_length=50, choices=TIER_CHOICES, unique=True)
    display_name_uk = models.CharField(max_length=100)
    display_name_en = models.CharField(max_length=100)
    display_name_pl = models.CharField(max_length=100)
    
    description_uk = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    description_pl = models.TextField(blank=True)
    
    order = models.PositiveIntegerField(default=0)
    is_popular = models.BooleanField(default=False, help_text="Позначити як 'Популярний'")
    
    class Meta:
        ordering = ['order']
        verbose_name = "Рівень цін"
        verbose_name_plural = "Рівні цін"
    
    def __str__(self):
        return f"{self.get_name_display()}"


class ServicePricing(models.Model):
    """Ціни для сервісів з детальною інформацією"""
    
    service_category = models.ForeignKey(
        ServiceCategory, 
        on_delete=models.CASCADE,
        related_name='pricing_options',
        verbose_name="Категорія сервісу"
    )
    
    tier = models.ForeignKey(
        PricingTier,
        on_delete=models.CASCADE,
        verbose_name="Рівень"
    )
    
    # Ціна
    price_from = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Мінімальна ціна в USD"
    )
    
    price_to = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Максимальна ціна (якщо діапазон). Залишити пустим для фіксованої ціни"
    )
    
    # Час виконання
    timeline_weeks_from = models.PositiveIntegerField(
        help_text="Мінімальний час в тижнях"
    )
    
    timeline_weeks_to = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Максимальний час в тижнях (якщо діапазон)"
    )
    
    # Що включено (багатомовно)
    features_included_uk = models.TextField(
        help_text="Що включено в цю ціну (українською). Кожна лінія = одна фіча"
    )
    features_included_en = models.TextField(
        help_text="What's included (English). Each line = one feature"
    )
    features_included_pl = models.TextField(
        help_text="Co jest włączone (Polish). Każda linia = jedna funkcja"
    )
    
    # Додаткова інфа для RAG
    complexity_level = models.CharField(
        max_length=20,
        choices=[
            ('simple', 'Простий'),
            ('medium', 'Середній'),
            ('complex', 'Складний'),
            ('enterprise', 'Корпоративний'),
        ],
        default='medium'
    )
    
    # Для кого підходить
    suitable_for_uk = models.TextField(
        blank=True,
        help_text="Для кого підходить цей пакет (українською)"
    )
    suitable_for_en = models.TextField(
        blank=True, 
        help_text="Who this package is suitable for (English)"
    )
    suitable_for_pl = models.TextField(
        blank=True,
        help_text="Dla kogo odpowiedni jest ten pakiet (Polish)"
    )
    
    # Метадані
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['service_category__title_en', 'tier__order', 'order']
        unique_together = ['service_category', 'tier']  # Один tier на сервіс
        verbose_name = "Ціна сервісу"
        verbose_name_plural = "Ціни сервісів"
        indexes = [
            models.Index(fields=['service_category', 'tier']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.service_category.title_en} - {self.tier.get_name_display()}"
    
    def get_price_display(self):
        """Повертає відформатовану ціну"""
        if self.price_to and self.price_to != self.price_from:
            return f"${int(self.price_from):,} - ${int(self.price_to):,}"
        return f"${int(self.price_from):,}"
    
    def get_timeline_display(self):
        """Повертає відформатований час"""
        if self.timeline_weeks_to and self.timeline_weeks_to != self.timeline_weeks_from:
            return f"{self.timeline_weeks_from}-{self.timeline_weeks_to} тижнів"
        return f"{self.timeline_weeks_from} тижнів"
    
    def get_features_list(self, lang='uk'):
        """Повертає список фіч як масив"""
        features_field = getattr(self, f'features_included_{lang}', self.features_included_uk)
        if features_field:
            return [f.strip() for f in features_field.split('\n') if f.strip()]
        return []
    
    def get_suitable_for(self, lang='uk'):
        """Повертає опис для кого підходить"""
        return getattr(self, f'suitable_for_{lang}', self.suitable_for_uk)


class QuoteRequest(models.Model):
    """Запити на прорахунок від клієнтів"""
    
    # Контакти клієнта
    client_name = models.CharField(max_length=100)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20, blank=True)
    client_company = models.CharField(max_length=100, blank=True)
    
    # Деталі запиту
    service_category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="Якщо AI зміг визначити категорію"
    )
    
    original_query = models.TextField(
        help_text="Оригінальний запит клієнта"
    )
    
    ai_analysis = models.TextField(
        blank=True,
        help_text="Аналіз AI про складність та вимоги"
    )
    
    suggested_pricing = models.ForeignKey(
        ServicePricing,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Запропоновані AI ціни"
    )
    
    # PDF та статус
    pdf_generated = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to='quotes/', blank=True, null=True)
    email_sent = models.BooleanField(default=False)
    
    # Консультація
    wants_consultation = models.BooleanField(default=False)
    consultation_scheduled = models.BooleanField(default=False)
    google_event_id = models.CharField(max_length=255, blank=True)
    
    # Метадані  
    session_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('new', 'Новий'),
            ('analyzed', 'Проаналізований'),
            ('quoted', 'Відправлено прорахунок'),
            ('consulted', 'Записано на консультацію'),
            ('converted', 'Конвертований'),
            ('closed', 'Закритий'),
        ],
        default='new'
    )
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_created']
        verbose_name = "Запит на прорахунок"
        verbose_name_plural = "Запити на прорахунки"
    
    def __str__(self):
        return f"{self.client_name} - {self.service_category or 'Не визначено'} - {self.get_status_display()}"