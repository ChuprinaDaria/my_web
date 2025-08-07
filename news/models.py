from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import uuid


class RSSSource(models.Model):
    """Джерела RSS новин"""
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('pl', 'Polski'),
        ('uk', 'Українська'),
    ]
    
    CATEGORY_CHOICES = [
        ('ai', 'AI & Machine Learning'),
        ('automation', 'Business Automation'),
        ('crm', 'CRM & Customer Management'),
        ('seo', 'SEO & Digital Marketing'),
        ('social', 'Social Media Marketing'),
        ('chatbots', 'Chatbots & Conversational AI'),
        ('ecommerce', 'E-commerce Development'),
        ('fintech', 'Fintech Automation'),
        ('corporate', 'Corporate & IT News'),
        ('general', 'General Tech News'),
    ]
    
    name = models.CharField(_('Назва джерела'), max_length=200)
    url = models.URLField(_('RSS URL'))
    language = models.CharField(_('Мова'), max_length=2, choices=LANGUAGE_CHOICES)
    category = models.CharField(_('Категорія'), max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(_('Опис джерела'), blank=True)
    is_active = models.BooleanField(_('Активне'), default=True)
    last_fetched = models.DateTimeField(_('Останнє оновлення'), null=True, blank=True)
    fetch_frequency = models.IntegerField(_('Частота оновлення (хв)'), default=60)
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('RSS Джерело')
        verbose_name_plural = _('RSS Джерела')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_language_display()})"


class NewsCategory(models.Model):
    """Категорії новин (тримовні)"""
    slug = models.SlugField(_('URL-слаг'), unique=True)
    icon = models.CharField(_('Іконка (emoji)'), max_length=10, default='📰')
    color = models.CharField(_('Колір'), max_length=7, default='#007bff')
    order = models.IntegerField(_('Порядок'), default=0)
    is_active = models.BooleanField(_('Активна'), default=True)
    
    # Назви та описи на трьох мовах
    name_en = models.CharField(_('Назва (EN)'), max_length=100)
    name_pl = models.CharField(_('Назва (PL)'), max_length=100)
    name_uk = models.CharField(_('Назва (UK)'), max_length=100)
    
    description_en = models.TextField(_('Опис (EN)'))
    description_pl = models.TextField(_('Опис (PL)'))
    description_uk = models.TextField(_('Опис (UK)'))
    
    # CTA на трьох мовах
    cta_title_en = models.CharField(_('CTA заголовок (EN)'), max_length=200, blank=True)
    cta_title_pl = models.CharField(_('CTA заголовок (PL)'), max_length=200, blank=True)
    cta_title_uk = models.CharField(_('CTA заголовок (UK)'), max_length=200, blank=True)
    
    cta_description_en = models.TextField(_('CTA опис (EN)'), blank=True)
    cta_description_pl = models.TextField(_('CTA опис (PL)'), blank=True)
    cta_description_uk = models.TextField(_('CTA опис (UK)'), blank=True)
    
    cta_button_text_en = models.CharField(_('Текст кнопки (EN)'), max_length=100, blank=True)
    cta_button_text_pl = models.CharField(_('Текст кнопки (PL)'), max_length=100, blank=True)
    cta_button_text_uk = models.CharField(_('Текст кнопки (UK)'), max_length=100, blank=True)
    
    cta_link = models.URLField(_('Посилання CTA'), blank=True)
    def get_absolute_url(self, language='uk'):
        """URL категорії для конкретної мови"""
        if language == 'en':
            return f'/en/news/category/{self.slug}/'
        elif language == 'pl':
            return f'/pl/news/category/{self.slug}/'
        else:  # uk
            return f'/uk/news/category/{self.slug}/'

    def get_cta_button_text(self, language='uk'):
        """Текст CTA кнопки для конкретної мови"""
        return getattr(self, f'cta_button_text_{language}', '')
    
    class Meta:
        verbose_name = _('Категорія новин')
        verbose_name_plural = _('Категорії новин')
        ordering = ['order', 'name_uk']
    
    def __str__(self):
        return self.name_uk
    
    def get_name(self, language='uk'):
        """Отримати назву для конкретної мови"""
        return getattr(self, f'name_{language}', self.name_uk)
    
    def get_description(self, language='uk'):
        """Отримати опис для конкретної мови"""
        return getattr(self, f'description_{language}', self.description_uk)
    
    def get_cta_title(self, language='uk'):
        """Отримати CTA заголовок для конкретної мови"""
        return getattr(self, f'cta_title_{language}', self.cta_title_uk)


class RawArticle(models.Model):
    """Сирі статті з RSS (перед обробкою AI)"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    source = models.ForeignKey(RSSSource, on_delete=models.CASCADE, related_name='raw_articles')
    
    # Оригінальні дані з RSS
    title = models.TextField(_('Заголовок'))
    content = models.TextField(_('Контент'), blank=True)
    summary = models.TextField(_('Короткий опис'), blank=True)
    original_url = models.URLField(_('Оригінальне посилання'))
    author = models.CharField(_('Автор'), max_length=200, blank=True)
    published_at = models.DateTimeField(_('Дата публікації'))
    
    # Метадані парсингу
    fetched_at = models.DateTimeField(_('Отримано'), auto_now_add=True)
    is_processed = models.BooleanField(_('Оброблено AI'), default=False)
    is_duplicate = models.BooleanField(_('Дублікат'), default=False)
    processing_attempts = models.IntegerField(_('Спроби обробки'), default=0)
    error_message = models.TextField(_('Помилка обробки'), blank=True)
    
    # Хеш для детекції дублікатів
    content_hash = models.CharField(_('Хеш контенту'), max_length=64, db_index=True)
    
    class Meta:
        verbose_name = _('Сира стаття')
        verbose_name_plural = _('Сирі статті')
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['content_hash']),
            models.Index(fields=['is_processed', 'is_duplicate']),
        ]
    
    def __str__(self):
        return f"{self.title[:50]}... ({self.source.name})"


class ProcessedArticle(models.Model):
    """Оброблені AI статті (тримовні)"""
    STATUS_CHOICES = [
        ('draft', _('Чернетка')),
        ('review', _('На перевірці')),
        ('published', _('Опубліковано')),
        ('archived', _('Архів')),
    ]
    
    PRIORITY_CHOICES = [
        (1, _('Низький')),
        (2, _('Середній')),
        (3, _('Високий')),
        (4, _('Критичний')),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    raw_article = models.OneToOneField(RawArticle, on_delete=models.CASCADE, related_name='processed')
    category = models.ForeignKey(NewsCategory, on_delete=models.CASCADE, related_name='articles')
    
    # Контент на трьох мовах (AI-перекладений)
    title_en = models.CharField(_('Заголовок (EN)'), max_length=300)
    title_pl = models.CharField(_('Заголовок (PL)'), max_length=300)
    title_uk = models.CharField(_('Заголовок (UK)'), max_length=300)
    
    summary_en = models.TextField(_('Короткий опис (EN)'))
    summary_pl = models.TextField(_('Короткий опис (PL)'))
    summary_uk = models.TextField(_('Короткий опис (UK)'))
    
    business_insight_en = models.TextField(_('Бізнес-інсайт (EN)'))
    business_insight_pl = models.TextField(_('Бізнес-інсайт (PL)'))
    business_insight_uk = models.TextField(_('Бізнес-інсайт (UK)'))
    
    local_context_en = models.TextField(_('Локальний контекст (EN)'), blank=True)
    local_context_pl = models.TextField(_('Локальний контекст (PL)'), blank=True)
    local_context_uk = models.TextField(_('Локальний контекст (UK)'), blank=True)
    
    # JSON поля для багатомовних списків
    key_takeaways_en = models.JSONField(_('Ключові висновки (EN)'), default=list)
    key_takeaways_pl = models.JSONField(_('Ключові висновки (PL)'), default=list)
    key_takeaways_uk = models.JSONField(_('Ключові висновки (UK)'), default=list)
    
    # SEO метадані для кожної мови
    meta_title_en = models.CharField(_('SEO заголовок (EN)'), max_length=60, blank=True)
    meta_title_pl = models.CharField(_('SEO заголовок (PL)'), max_length=60, blank=True)
    meta_title_uk = models.CharField(_('SEO заголовок (UK)'), max_length=60, blank=True)
    
    meta_description_en = models.CharField(_('SEO опис (EN)'), max_length=160, blank=True)
    meta_description_pl = models.CharField(_('SEO опис (PL)'), max_length=160, blank=True)
    meta_description_uk = models.CharField(_('SEO опис (UK)'), max_length=160, blank=True)
    
    # AI згенеровані зображення
    ai_image_url = models.URLField(_('AI зображення'), blank=True)
    ai_image_prompt_en = models.TextField(_('Промпт зображення (EN)'), blank=True)
    ai_image_prompt_pl = models.TextField(_('Промпт зображення (PL)'), blank=True)
    ai_image_prompt_uk = models.TextField(_('Промпт зображення (UK)'), blank=True)
    
    # CTA для статті на трьох мовах
    cta_title_en = models.CharField(_('CTA заголовок (EN)'), max_length=200, blank=True)
    cta_title_pl = models.CharField(_('CTA заголовок (PL)'), max_length=200, blank=True)
    cta_title_uk = models.CharField(_('CTA заголовок (UK)'), max_length=200, blank=True)
    
    cta_description_en = models.TextField(_('CTA опис (EN)'), blank=True)
    cta_description_pl = models.TextField(_('CTA опис (PL)'), blank=True)
    cta_description_uk = models.TextField(_('CTA опис (UK)'), blank=True)
    
    # CTA кнопки - JSON з текстами для всіх мов
    # Структура: [{"text_en": "...", "text_pl": "...", "text_uk": "...", "url": "..."}]
    cta_buttons = models.JSONField(_('CTA кнопки'), default=list)
    
    # Статус та метрики
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.IntegerField(_('Пріоритет'), choices=PRIORITY_CHOICES, default=2)
    
    # Перегляди по мовах
    views_count_en = models.IntegerField(_('Перегляди (EN)'), default=0)
    views_count_pl = models.IntegerField(_('Перегляди (PL)'), default=0)
    views_count_uk = models.IntegerField(_('Перегляди (UK)'), default=0)
    
    shares_count = models.IntegerField(_('Поділитися'), default=0)
    
    # AI налаштування
    ai_model_used = models.CharField(_('AI модель'), max_length=100, blank=True)
    ai_cost = models.DecimalField(_('Вартість AI'), max_digits=10, decimal_places=4, default=0)
    ai_processing_time = models.FloatField(_('Час обробки AI (сек)'), null=True, blank=True)
    
    # Дати
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Оновлено'), auto_now=True)
    published_at = models.DateTimeField(_('Опубліковано'), null=True, blank=True)
    def get_meta_title(self, language='uk'):
        """Meta заголовок для конкретної мови"""
        meta_title = getattr(self, f'meta_title_{language}', '')
        return meta_title or self.get_title(language)

    def get_meta_description(self, language='uk'):
        """Meta опис для конкретної мови"""
        meta_desc = getattr(self, f'meta_description_{language}', '')
        return meta_desc or self.get_summary(language)[:160]

    def get_reading_time(self):
        """Час читання статті в хвилинах"""
        # Загальна довжина контенту
        total_content = (
            len(self.get_business_insight()) + 
            len(self.get_summary()) + 
            len(self.get_local_context() or '')
        )
        
        # Приблизно 5 символів на слово, 200 слів за хвилину
        words = total_content // 5
        minutes = max(1, words // 200)
        return minutes

    def get_cta_title(self, language='uk'):
        """CTA заголовок для конкретної мови"""
        return getattr(self, f'cta_title_{language}', '')

    def get_cta_description(self, language='uk'):
        """CTA опис для конкретної мови"""
        return getattr(self, f'cta_description_{language}', '')

    def get_absolute_url(self, language='uk'):
        """URL для конкретної мови"""
        if language == 'en':
            return f'/en/news/article/{self.uuid}/'
        elif language == 'pl':
            return f'/pl/news/article/{self.uuid}/'
        else:  # uk
            return f'/uk/news/article/{self.uuid}/'

    @property 
    def original_source_name(self):
        """Назва оригінального джерела"""
        return self.raw_article.source.name

    @property
    def original_source_url(self):
        """URL оригінального джерела"""
        return self.raw_article.original_url

    def is_fresh(self, days=7):
        """Чи стаття свіжа (менше ніж X днів)"""
        if not self.published_at:
            return False
        
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.published_at >= cutoff_date

    def get_priority_display(self):
        """Текстове відображення пріоритету"""
        priority_map = {
            1: "🔵 Низький",
            2: "🟡 Середній", 
            3: "🟠 Високий",
            4: "🔴 Критичний"
        }
        return priority_map.get(self.priority, "🔵 Низький")

    def get_social_share_urls(self, request=None):
        """Повертає URL для соціальних мереж"""
        if request:
            full_url = request.build_absolute_uri(self.get_absolute_url())
            title = self.get_title()
        else:
            full_url = f"https://lazysoft.dev{self.get_absolute_url()}"
            title = self.title_uk
        
        return {
            'facebook': f"https://www.facebook.com/sharer/sharer.php?u={full_url}",
            'twitter': f"https://twitter.com/intent/tweet?url={full_url}&text={title}",
            'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={full_url}",
            'telegram': f"https://t.me/share/url?url={full_url}&text={title}"
        }
    class Meta:
        verbose_name = _('Оброблена стаття')
        verbose_name_plural = _('Оброблені статті')
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['published_at']),
        ]
    
    def __str__(self):
        return self.title_uk
    
    def get_absolute_url(self, language='uk'):
        """URL для конкретної мови"""
        return reverse('news:article_detail', kwargs={'uuid': self.uuid, 'lang': language})
    
    def get_title(self, language='uk'):
        """Заголовок для конкретної мови"""
        return getattr(self, f'title_{language}', self.title_uk)
    
    def get_summary(self, language='uk'):
        """Короткий опис для конкретної мови"""
        return getattr(self, f'summary_{language}', self.summary_uk)
    
    def get_business_insight(self, language='uk'):
        """Бізнес-інсайт для конкретної мови"""
        return getattr(self, f'business_insight_{language}', self.business_insight_uk)
    
    def get_local_context(self, language='uk'):
        """Локальний контекст для конкретної мови"""
        return getattr(self, f'local_context_{language}', self.local_context_uk)
    
    def get_key_takeaways(self, language='uk'):
        """Ключові висновки для конкретної мови"""
        return getattr(self, f'key_takeaways_{language}', self.key_takeaways_uk)
    
    def get_total_views(self):
        """Загальна кількість переглядів"""
        return self.views_count_en + self.views_count_pl + self.views_count_uk
    
    def increment_views(self, language='uk'):
        """Збільшити лічильник переглядів для мови"""
        field_name = f'views_count_{language}'
        if hasattr(self, field_name):
            setattr(self, field_name, getattr(self, field_name) + 1)
            self.save(update_fields=[field_name])
    
    def publish(self):
        """Опублікувати статтю"""
        self.status = 'published'
        self.published_at = timezone.now()
        self.save()


class DailyDigest(models.Model):
    """Щоденні дайджести (тримовні)"""
    date = models.DateField(_('Дата'), unique=True)
    
    # Заголовки на трьох мовах
    title_en = models.CharField(_('Заголовок (EN)'), max_length=300)
    title_pl = models.CharField(_('Заголовок (PL)'), max_length=300)
    title_uk = models.CharField(_('Заголовок (UK)'), max_length=300)
    
    # Вступний текст
    intro_text_en = models.TextField(_('Вступний текст (EN)'))
    intro_text_pl = models.TextField(_('Вступний текст (PL)'))
    intro_text_uk = models.TextField(_('Вступний текст (UK)'))
    
    articles = models.ManyToManyField(ProcessedArticle, related_name='digests')
    
    # AI-генерований контент
    summary_en = models.TextField(_('Загальний огляд (EN)'))
    summary_pl = models.TextField(_('Загальний огляд (PL)'))
    summary_uk = models.TextField(_('Загальний огляд (UK)'))
    
    key_insights_en = models.JSONField(_('Ключові інсайти (EN)'), default=list)
    key_insights_pl = models.JSONField(_('Ключові інсайти (PL)'), default=list)
    key_insights_uk = models.JSONField(_('Ключові інсайти (UK)'), default=list)
    
    market_trends_en = models.TextField(_('Тренди ринку (EN)'), blank=True)
    market_trends_pl = models.TextField(_('Тренди ринку (PL)'), blank=True)
    market_trends_uk = models.TextField(_('Тренди ринку (UK)'), blank=True)
    
    # Статистика
    total_articles = models.IntegerField(_('Всього статей'), default=0)
    top_categories = models.JSONField(_('Топ категорії'), default=list)
    
    # Статус
    is_generated = models.BooleanField(_('Згенеровано'), default=False)
    is_published = models.BooleanField(_('Опубліковано'), default=False)
    
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    published_at = models.DateTimeField(_('Опубліковано'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Щоденний дайджест')
        verbose_name_plural = _('Щоденні дайджести')
        ordering = ['-date']
    
    def __str__(self):
        return f"Дайджест {self.date}"
    
    def get_absolute_url(self, language='uk'):
        return reverse('news:digest_detail', kwargs={'date': self.date, 'lang': language})
    
    def get_title(self, language='uk'):
        """Заголовок для конкретної мови"""
        return getattr(self, f'title_{language}', self.title_uk)


class AIProcessingLog(models.Model):
    """Лог обробки AI для моніторингу та налагодження"""
    LOG_TYPES = [
        ('translation', _('Переклад')),
        ('categorization', _('Категоризація')),
        ('analysis', _('Аналіз')),
        ('image_generation', _('Генерація зображень')),
        ('cta_generation', _('Генерація CTA')),
        ('digest_generation', _('Генерація дайджесту')),
    ]
    
    article = models.ForeignKey(RawArticle, on_delete=models.CASCADE, related_name='ai_logs')
    log_type = models.CharField(_('Тип обробки'), max_length=20, choices=LOG_TYPES)
    model_used = models.CharField(_('Модель'), max_length=100)
    target_language = models.CharField(_('Цільова мова'), max_length=2, blank=True)
    
    # Вхідні дані
    input_tokens = models.IntegerField(_('Вхідні токени'), default=0)
    input_data = models.JSONField(_('Вхідні дані'), default=dict)
    
    # Результат
    output_tokens = models.IntegerField(_('Вихідні токени'), default=0)
    output_data = models.JSONField(_('Результат'), default=dict)
    
    # Метрики
    processing_time = models.FloatField(_('Час обробки (сек)'))
    cost = models.DecimalField(_('Вартість'), max_digits=10, decimal_places=6, default=0)
    success = models.BooleanField(_('Успішно'), default=True)
    error_message = models.TextField(_('Помилка'), blank=True)
    
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('AI лог')
        verbose_name_plural = _('AI логи')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_log_type_display()} - {self.model_used} ({self.created_at})"


class TranslationCache(models.Model):
    """Кеш перекладів для економії на API викликах"""
    source_text_hash = models.CharField(_('Хеш оригінального тексту'), max_length=64, db_index=True)
    source_language = models.CharField(_('Мова оригіналу'), max_length=2)
    target_language = models.CharField(_('Цільова мова'), max_length=2)
    
    source_text = models.TextField(_('Оригінальний текст'))
    translated_text = models.TextField(_('Перекладений текст'))
    
    translator_used = models.CharField(_('Перекладач'), max_length=50)  # 'openai', 'google', 'deepl'
    quality_score = models.FloatField(_('Оцінка якості'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    used_count = models.IntegerField(_('Використано разів'), default=1)
    last_used = models.DateTimeField(_('Останнє використання'), auto_now=True)
    
    class Meta:
        verbose_name = _('Кеш перекладів')
        verbose_name_plural = _('Кеш перекладів')
        unique_together = ['source_text_hash', 'source_language', 'target_language']
        indexes = [
            models.Index(fields=['source_text_hash', 'source_language', 'target_language']),
        ]
    
    def __str__(self):
        return f"{self.source_language} -> {self.target_language} ({self.created_at})"