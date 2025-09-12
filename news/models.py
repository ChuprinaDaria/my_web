from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, F, Avg
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.urls import reverse
from django.utils.translation import override
from django.conf import settings
from django.utils.text import slugify
from django.db import models
from django.utils import timezone

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
    author = models.CharField(_('Автор'), max_length=500, blank=True)
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
    
    # Бізнес можливості
    business_opportunities_en = models.TextField(_('Бізнес можливості (EN)'), blank=True)
    business_opportunities_pl = models.TextField(_('Бізнес можливості (PL)'), blank=True)
    business_opportunities_uk = models.TextField(_('Бізнес можливості (UK)'), blank=True)
    
    # LAZYSOFT рекомендації
    lazysoft_recommendations_en = models.TextField(_('Рекомендації LAZYSOFT (EN)'), blank=True)
    lazysoft_recommendations_pl = models.TextField(_('Рекомендації LAZYSOFT (PL)'), blank=True)
    lazysoft_recommendations_uk = models.TextField(_('Рекомендації LAZYSOFT (UK)'), blank=True)
    
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
    ai_image_url = models.URLField(_('AI зображення'), blank=True, max_length=500)
    ai_image_prompt_en = models.TextField(_('Промпт зображення (EN)'), blank=True)
    ai_image_prompt_uk = models.TextField(_('Промпт зображення (UK)'), blank=True)
    ai_image_prompt_pl = models.TextField(_('Промпт зображення (PL)'), blank=True)

    # === НОВІ ПОЛЯ для Enhanced AI інсайтів ===
    
    # Цікавинки та факти (JSON поля)
    interesting_facts_en = models.JSONField(_('Цікавинки (EN)'), default=list)
    interesting_facts_pl = models.JSONField(_('Цікавинки (PL)'), default=list)
    interesting_facts_uk = models.JSONField(_('Цікавинки (UK)'), default=list)
    
    # Додаткові поля для Full Article Parser
    original_word_count = models.IntegerField(_('Кількість слів оригіналу'), default=0)
    reading_time = models.IntegerField(_('Час читання (хв)'), default=5)
    full_content_parsed = models.BooleanField(_('Повний контент спарсений'), default=False)
    
    # Повний контент для топ-статей (адаптований AI)
    full_content_en = models.TextField(_('Повний контент (EN)'), blank=True)
    full_content_pl = models.TextField(_('Повний контент (PL)'), blank=True)
    full_content_uk = models.TextField(_('Повний контент (UK)'), blank=True)
    
    # Флаги топ-статей
    is_top_article = models.BooleanField(_('Топ стаття'), default=False)
    article_rank = models.IntegerField(_('Ранг у топ-5'), null=True, blank=True, 
                                     help_text='Позиція статті в топ-5 (1-5)')
    
    # Метадані для топ-статей
    top_selection_date = models.DateField(_('Дата відбору в топ'), null=True, blank=True)
    relevance_score = models.FloatField(_('Скор релевантності'), null=True, blank=True,
                                      help_text='Скор від AudienceAnalyzer (1-10)')

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
    
    shares_count = models.IntegerField(_('Поділитись'), default=0)
    
    # Унікальний слаг для SEO та URL
    slug = models.SlugField(_('Slug'), max_length=220, blank=True, unique=True, help_text='Для /news/top/<slug>/')

    # AI налаштування
    ai_model_used = models.CharField(_('AI модель'), max_length=100, blank=True)
    ai_cost = models.DecimalField(_('Вартість AI'), max_digits=10, decimal_places=4, default=0)
    ai_processing_time = models.FloatField(_('Час обробки AI (сек)'), null=True, blank=True)
    
    # 🏷️ СИСТЕМА ВНУТРІШНІХ ТЕГІВ для крос-промоції
    tags = models.ManyToManyField(
        'core.Tag',
        blank=True,
        related_name='articles',
        help_text="Внутрішні теги для крос-видачі з проєктами та сервісами"
    )

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

    def get_absolute_url(self, language=None):
        if language:
            # перемикаємо контекст мови, щоб reverse підставив префікс /uk /en /pl
            with override(language):
                return reverse('news:article_detail', kwargs={'uuid': self.uuid})
        return reverse('news:article_detail', kwargs={'uuid': self.uuid})

    @property 
    def original_source_name(self):
        """Назва оригінального джерела"""
        return self.raw_article.source.name

    @property
    def original_source_url(self):
        """URL оригінального джерела"""
        return self.raw_article.original_url
    
    @property
    def source_url(self):
        """Посилання на оригінальну статтю - ГОТОВО!"""
        return self.raw_article.original_url
    
    @property  
    def source_domain(self):
        """Домен джерела для красивого відображення"""
        from urllib.parse import urlparse
        try:
            domain = urlparse(self.source_url).netloc
            return domain.replace('www.', '').title()
        except:
            return "Unknown Source"

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
    
    def __str__(self):
        return self.title_uk
    
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

    # Додати ці методи в ProcessedArticle клас ПІСЛЯ існуючих методів:

    def get_interesting_facts(self, language='uk'):
        """Цікавинки для конкретної мови"""
        return getattr(self, f'interesting_facts_{language}', [])
    
    def get_business_opportunities(self, language='uk'):
        """Бізнес можливості для конкретної мови"""
        return getattr(self, f'business_opportunities_{language}', '')
    
    def get_lazysoft_recommendations(self, language='uk'):
        """LAZYSOFT рекомендації для конкретної мови"""
        return getattr(self, f'lazysoft_recommendations_{language}', '')
    
    def get_ai_image_prompt(self, language='uk'):
        """AI промпт для зображення конкретною мовою"""
        return getattr(self, f'ai_image_prompt_{language}', '')
    
    def get_enhanced_reading_time(self):
        """Оновлений розрахунок часу читання з урахуванням нових полів"""
        if self.reading_time and self.reading_time > 0:
            return self.reading_time  # Якщо є збережений час
        
        # Розраховуємо на основі всього контенту
        total_content = (
            len(self.get_business_insight()) + 
            len(self.get_summary()) + 
            len(self.get_local_context() or '') +
            len(self.get_business_opportunities() or '') +
            len(self.get_lazysoft_recommendations() or '')
        )
        
        # Додаємо довжину списків
        facts = self.get_interesting_facts()
        takeaways = self.get_key_takeaways()
        total_content += sum(len(fact) for fact in facts)
        total_content += sum(len(takeaway) for takeaway in takeaways)
        
        # Приблизно 5 символів на слово, 200 слів за хвилину
        words = total_content // 5
        minutes = max(1, words // 200)
        return minutes
    
    def has_enhanced_insights(self):
        """Перевіряє чи є розширені LAZYSOFT інсайти"""
        return bool(
            self.get_interesting_facts() or 
            self.get_business_opportunities() or 
            self.get_lazysoft_recommendations()
        )
    
    def get_content_completeness_score(self):
        """Оцінка повноти контенту (0-100%)"""
        score = 0
        max_score = 10
        
        # Базовий контент (40%)
        if self.get_title(): score += 1
        if self.get_summary(): score += 1
        if self.get_business_insight(): score += 1
        if self.ai_image_url: score += 1
        
        # SEO (20%)
        if self.get_meta_title(): score += 1
        if self.get_meta_description(): score += 1
        
        # Enhanced інсайти (30%)
        if self.get_interesting_facts(): score += 1
        if self.get_business_opportunities(): score += 1
        if self.get_lazysoft_recommendations(): score += 1
        
        # Додаткові поля (10%)
        if self.full_content_parsed: score += 1
        
        return (score / max_score) * 100

    # === ПОКРАЩЕНІ МЕТОДИ КРОС-ПРОМОЦІЇ (БЕЗ ЛОМАННЯ ІСНУЮЧОГО) ===
    
    def get_related_projects(self, limit=3):
        """Повертає проєкти з такими ж тегами"""
        if not self.tags.exists():
            return []
        
        try:
            # Використовуємо apps.get_model замість прямого import
            from django.apps import apps
            Project = apps.get_model('projects', 'Project')
            return Project.objects.filter(
                tags__in=self.tags.all(),
                is_active=True
            ).distinct().exclude(
                # Можна додати додаткові фільтри
            ).order_by('-priority', '-project_date')[:limit]
        except LookupError:
            # Якщо модель Project не знайдена
            return []
    
    def get_related_services(self, limit=3):
        """Повертає сервіси з такими ж тегами"""
        if not self.tags.exists():
            return []
        
        try:
            from django.apps import apps
            Service = apps.get_model('services', 'Service')
            return Service.objects.filter(
                tags__in=self.tags.all(),
                is_active=True
            ).distinct().order_by('-date_created')[:limit]
        except LookupError:
            return []
    
    def get_cross_promotion_content(self, limit=6):
        """
        Повертає змішаний контент для крос-промоції
        Використовується в шаблонах для показу пов'язаного контенту
        """
        content = []
        
        # Додаємо пов'язані проєкти
        related_projects = self.get_related_projects(limit=3)
        for project in related_projects:
            content.append({
                'type': 'project',
                'title': project.title_uk,
                'short_description': getattr(project, 'short_description_uk', ''),
                'url': f'/projects/{project.slug}/',
                'image': project.featured_image.url if project.featured_image else None,
                'badges': project.get_all_badges('uk'),
                'object': project
            })
        
        # Додаємо пов'язані сервіси
        related_services = self.get_related_services(limit=3)
        for service in related_services:
            content.append({
                'type': 'service', 
                'title': service.title_uk,
                'short_description': getattr(service, 'short_description_uk', ''),
                'url': f'/services/{service.slug}/',
                'image': service.icon.url if service.icon else None,
                'object': service
            })
        
        return content[:limit]
    

    def save(self, *args, **kwargs):    # автослаг тільки якщо немає й стаття топова або дуже релевантна
        if not self.slug:
            base = (self.meta_title_uk or self.title_uk or self.title_en or self.title_pl or '')[:180]
            if base:
                self.slug = slugify(f"{base}-{str(self.uuid)[:8]}")
  # захист правила генерації зображення:
  # зображення дозволене для всіх статей (видалено обмеження на топові статті)
  # if self.ai_image_url and not (self.is_top_article and self.full_content_parsed):
  #     self.ai_image_url = ''
        super().save(*args, **kwargs)


    # === АВТОМАТИЧНЕ ПРИЗНАЧЕННЯ ТЕГІВ ===
    
    def auto_assign_tags(self):
        """Автоматично призначає теги на основі контенту статті"""
        # Мапінг ключових слів на слаги тегів
        keyword_mapping = {
            'AI': ['ai', 'machine-learning', 'artificial-intelligence'],
            'automation': ['automation', 'business-automation'],
            'chatbot': ['chatbots', 'ai', 'conversational-ai'],
            'CRM': ['crm', 'customer-management'],
            'SEO': ['seo', 'digital-marketing'],
            'social media': ['social-media', 'marketing'],
            'e-commerce': ['ecommerce', 'online-store'],
            'fintech': ['fintech', 'financial-technology'],
            'blockchain': ['blockchain', 'crypto'],
            'API': ['api', 'integration'],
            'cloud': ['cloud-computing', 'aws', 'azure'],
            'mobile': ['mobile-development', 'app'],
            'web development': ['web-development', 'frontend', 'backend'],
            'database': ['database', 'sql', 'nosql'],
            'security': ['cybersecurity', 'data-protection'],
            'analytics': ['analytics', 'data-science'],
            'startup': ['startup', 'business'],
            'investment': ['investment', 'funding'],
        }
        
        # Об'єднуємо весь контент статті для аналізу
        content_to_analyze = f"""
        {self.get_title()} 
        {self.get_summary()} 
        {self.get_business_insight()}
        {' '.join(self.get_key_takeaways())}
        """.lower()
        
        suggested_tag_slugs = set()
        
        # Шукаємо ключові слова в контенті
        for keyword, tag_slugs in keyword_mapping.items():
            if keyword.lower() in content_to_analyze:
                suggested_tag_slugs.update(tag_slugs)
        
        # Додаємо теги на основі категорії статті
        category_tag_mapping = {
            'ai': ['ai', 'machine-learning'],
            'automation': ['automation', 'business-automation'],
            'crm': ['crm', 'customer-management'],
            'seo': ['seo', 'digital-marketing'],
            'social': ['social-media', 'marketing'],
            'chatbots': ['chatbots', 'ai'],
            'ecommerce': ['ecommerce', 'online-store'],
            'fintech': ['fintech', 'financial-technology'],
        }
        
        # Додаємо теги на основі RSS категорії
        rss_category = self.raw_article.source.category
        if rss_category in category_tag_mapping:
            suggested_tag_slugs.update(category_tag_mapping[rss_category])
        
        # Знаходимо та призначаємо теги
        if suggested_tag_slugs:
            try:
                from django.apps import apps
                Tag = apps.get_model('core', 'Tag')
                
                existing_tags = Tag.objects.filter(
                    slug__in=suggested_tag_slugs,
                    is_active=True
                )
                
                # Додаємо теги до статті (не видаляючи існуючі)
                self.tags.add(*existing_tags)
                
                return list(existing_tags.values_list('slug', flat=True))
            except LookupError:
                return []
        
        return []
    
    def get_smart_cta(self, language='uk'):
        """Генерує розумний CTA на основі тегів статті"""
        # Мапінг тегів на CTA
        tag_cta_mapping = {
            'ai': {
                'title_uk': 'Хочете впровадити AI у ваш бізнес?',
                'title_en': 'Want to implement AI in your business?',
                'title_pl': 'Chcesz wdrożyć AI w swoim biznesie?',
                'url': '/services/ai-development/',
                'button_text_uk': 'Замовити консультацію',
                'button_text_en': 'Get Consultation',
                'button_text_pl': 'Zamów konsultację'
            },
            'automation': {
                'title_uk': 'Автоматизуйте ваші бізнес-процеси',
                'title_en': 'Automate your business processes',
                'title_pl': 'Zautomatyzuj swoje procesy biznesowe',
                'url': '/services/business-automation/',
                'button_text_uk': 'Дізнатися більше',
                'button_text_en': 'Learn More',
                'button_text_pl': 'Dowiedz się więcej'
            },
            'crm': {
                'title_uk': 'Потрібна CRM система?',
                'title_en': 'Need a CRM system?',
                'title_pl': 'Potrzebujesz systemu CRM?',
                'url': '/services/crm-development/',
                'button_text_uk': 'Подивитися рішення',
                'button_text_en': 'View Solutions',
                'button_text_pl': 'Zobacz rozwiązania'
            },
            'ecommerce': {
                'title_uk': 'Створимо інтернет-магазин для вас',
                'title_en': "We'll create an online store for you",
                'title_pl': 'Stworzymy dla Ciebie sklep internetowy',
                'url': '/services/ecommerce-development/',
                'button_text_uk': 'Розпочати проєкт',
                'button_text_en': 'Start Project',
                'button_text_pl': 'Rozpocznij projekt'
            }
        }
        
        # Шукаємо відповідний CTA на основі тегів статті
        for tag in self.tags.all():
            if tag.slug in tag_cta_mapping:
                cta_data = tag_cta_mapping[tag.slug]
                return {
                    'title': cta_data.get(f'title_{language}', cta_data['title_uk']),
                    'url': cta_data['url'],
                    'button_text': cta_data.get(f'button_text_{language}', cta_data['button_text_uk'])
                }
        
        # Дефолтний CTA якщо нічого не знайдено
        default_cta = {
            'uk': {
                'title': 'Потрібна допомога з розробкою?',
                'button_text': 'Зв\'язатися з нами'
            },
            'en': {
                'title': 'Need help with development?',
                'button_text': 'Contact us'
            },
            'pl': {
                'title': 'Potrzebujesz pomocy z rozwojem?',
                'button_text': 'Skontaktuj się z nami'
            }
        }
        
        return {
            'title': default_cta[language]['title'],
            'url': '/contact/',
            'button_text': default_cta[language]['button_text']
        }
    
    def get_tag_performance_metrics(self):
        """Метрики ефективності тегів для цієї статті"""
        if not self.tags.exists():
            return {}
        
        metrics = {}
        for tag in self.tags.all():
            # Рахуємо метрики для кожного тегу
            tag_articles = ProcessedArticle.objects.filter(tags=tag)
            
            metrics[tag.slug] = {
                'total_articles': tag_articles.count(),
                'avg_views': tag_articles.aggregate(
                    avg_views=Avg(F('views_count_uk') + F('views_count_en') + F('views_count_pl'))
                )['avg_views'] or 0,
                'total_views': tag_articles.aggregate(
                    total_views=Sum(F('views_count_uk') + F('views_count_en') + F('views_count_pl'))
                )['total_views'] or 0,
            }
        
        return metrics
    
    def get_ai_processing_cost(self):
        """Повертає загальну вартість AI обробки для цієї статті"""
        if not hasattr(self, 'raw_article'):
            return 0.0
        
        from django.db.models import Sum
        total_cost = self.raw_article.ai_logs.aggregate(
            total_cost=Sum('cost')
        )['total_cost'] or 0
        
        return float(total_cost)
    
    def get_ai_processing_time(self):
        """Повертає загальний час AI обробки для цієї статті"""
        if not hasattr(self, 'raw_article'):
            return 0.0
        
        from django.db.models import Sum
        total_time = self.raw_article.ai_logs.aggregate(
            total_time=Sum('processing_time')
        )['total_time'] or 0
        
        return float(total_time)
    
    def get_ai_operations_count(self):
        """Повертає кількість AI операцій для цієї статті"""
        if not hasattr(self, 'raw_article'):
            return 0
        
        return self.raw_article.ai_logs.count()

    # === НОВІ МЕТОДИ для топ-статей ===
    
    def get_full_content(self, language='uk'):
        """Повний контент для конкретної мови (для топ-статей)"""
        return getattr(self, f'full_content_{language}', '')
    
    def is_top_quality(self):
        """Перевіряє чи стаття топ-якості"""
        return self.is_top_article and bool(self.get_full_content())
    
    def get_top_rank_display(self):
        """Красиве відображення рангу"""
        if not self.is_top_article or not self.article_rank:
            return ""
        
        rank_icons = {1: "🥇", 2: "🥈", 3: "🥉", 4: "🎖️", 5: "🏅"}
        icon = rank_icons.get(self.article_rank, "📊")
        return f"{icon} #{self.article_rank}"
    
    def get_content_for_display(self, language='uk'):
        """Повертає контент для відображення (повний для топ, короткий для звичайних)"""
        if self.is_top_article and self.get_full_content(language):
            return self.get_full_content(language)
        return self.get_business_insight(language)
    
    @classmethod
    def get_top_articles(cls, date=None, limit=5):
        """Отримує топ-статті за датою"""
        queryset = cls.objects.filter(is_top_article=True, status='published')
        
        if date:
            queryset = queryset.filter(top_selection_date=date)
        
        return queryset.order_by('article_rank')[:limit]
    
    @classmethod
    def get_regular_articles(cls, date=None, limit=20):
        """Отримує звичайні статті (не топ)"""
        queryset = cls.objects.filter(is_top_article=False, status='published')
        
        if date:
            queryset = queryset.filter(published_at__date=date)
        
        return queryset.order_by('-priority', '-published_at')[:limit]

    class Meta:
        verbose_name = _('Оброблена стаття')
        verbose_name_plural = _('Оброблені статті')
        ordering = ['-is_top_article', '-article_rank', '-priority', '-created_at']
        indexes = [
            models.Index(fields=['slug']),                              # пошук/деталка за slug
            models.Index(fields=['status', 'category']),                # фільтри списків
            models.Index(fields=['status', 'published_at']),            # архів/лента
            models.Index(fields=['published_at']),                      # сортування по даті
            models.Index(fields=['is_top_article', 'article_rank']),    # топ-5 швидко
            models.Index(fields=['top_selection_date']),                # вибірка топів за датою
        ]


class Comment(models.Model):
    """Коментарі з реплаями, банами та авто-модерацією"""
    PROVIDERS = [
        ('email', 'Email/Password'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram'),
    ]
    article = models.ForeignKey(ProcessedArticle, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    provider = models.CharField(max_length=20, choices=PROVIDERS, default='email')
    display_name = models.CharField(max_length=80, blank=True)  # якщо соц-логін не повернув name
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    body = models.TextField()
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def block(self):
        self.is_blocked = True
        self.save(update_fields=['is_blocked', 'updated_at'])


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
        ('tag_assignment', _('Призначення тегів')),  # НОВИЙ ТИП
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


class ROIAnalytics(models.Model):
    """Аналітика ROI для Dashboard - показуємо клієнтам наші метрики"""
    
    # Період аналізу
    date = models.DateField(_('Дата'), unique=True)
    
    # === ЕКОНОМІЯ ЧАСУ ===
    manual_hours_saved = models.FloatField(
        _('Годин заощаджено (ручна робота)'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(200)]  # Max 200h/month
    )
    ai_processing_time = models.FloatField(
        _('Час AI обробки (годин)'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)]  # Max 50h/month
    )
    time_efficiency = models.FloatField(
        _('Ефективність часу (%)'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000)]  # Max 1000%
    )
    
    # === ФІНАНСОВА ЕКОНОМІЯ ===
    content_manager_cost_saved = models.DecimalField(
        _('Економія на контент-менеджері'), 
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10000)]  # Max $10k/month
    )
    smm_specialist_cost_saved = models.DecimalField(
        _('Економія на SMM'), 
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    copywriter_cost_saved = models.DecimalField(
        _('Економія на копірайтері'), 
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    ai_api_costs = models.DecimalField(
        _('Витрати на AI API'), 
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000)]  # Max $1k/month
    )
    net_savings = models.DecimalField(
        _('Чиста економія'), 
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(-1000), MaxValueValidator(50000)]  # -$1k to $50k
    )
    
    # === ТРАФІК ТА ЗАЛУЧЕННЯ ===
    organic_traffic_increase = models.IntegerField(_('Приріст органічного трафіку'), default=0)
    social_engagement_increase = models.IntegerField(_('Приріст engagement соцмереж'), default=0)
    new_leads_generated = models.IntegerField(_('Нових лідів згенеровано'), default=0)
    bounce_rate_improvement = models.FloatField(_('Покращення bounce rate (%)'), default=0)
    
    # === AI МЕТРИКИ (ВИПРАВЛЕНІ!) ===
    articles_processed = models.IntegerField(
        _('Статей оброблено AI'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]  # Max 100 articles/month
    )
    translations_made = models.IntegerField(
        _('Перекладів зроблено'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(300)]  # Max 300 translations/month
    )
    social_posts_generated = models.IntegerField(
        _('Соцмереж постів згенеровано'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(200)]  # Max 200 posts/month
    )
    images_generated = models.IntegerField(
        _('AI зображень згенеровано'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(500)]  # Max 500 images/month
    )
    tags_assigned = models.IntegerField(
        _('Тегів призначено автоматично'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000)]  # Max 1000 tags/month
    )
    
    # === НОВІ ПОЛЯ КЛЮЧОВИХ ВИСНОВКІВ ===
    key_takeaways_en = models.JSONField(_('Ключові висновки (EN)'), default=list)
    key_takeaways_uk = models.JSONField(_('Ключові висновки (UK)'), default=list) 
    key_takeaways_pl = models.JSONField(_('Ключові висновки (PL)'), default=list)
    
    # === ЯКІСТЬ КОНТЕНТУ ===
    avg_article_rating = models.FloatField(_('Середня оцінка статей'), default=0)
    seo_score_improvement = models.FloatField(_('Покращення SEO скору'), default=0)
    content_uniqueness = models.FloatField(_('Унікальність контенту (%)'), default=0)
    
    # === НОВІ ПОЛЯ для тегової аналітики ===
    top_performing_tags = models.JSONField(_('Топ теги за ефективністю'), default=list)
    tag_engagement_stats = models.JSONField(_('Статистика залучення по тегах'), default=dict)
    cross_promotion_success_rate = models.FloatField(_('Успішність крос-промоції (%)'), default=0)
    
    # Метадані
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Оновлено'), auto_now=True)
    
    class Meta:
        verbose_name = _('ROI Аналітика')
        verbose_name_plural = _('ROI Аналітика')
        ordering = ['-date']
    
    def __str__(self):
        return f"ROI {self.date}"
    
    @property
    def total_cost_savings(self):
        """Загальна економія коштів - ВИПРАВЛЕНО"""
        return (
            self.content_manager_cost_saved + 
            self.smm_specialist_cost_saved + 
            self.copywriter_cost_saved - 
            self.ai_api_costs
        )
    
    @property
    def roi_percentage(self):
        """ROI у відсотках - ВИПРАВЛЕНО"""
        if self.ai_api_costs > 0:
            return ((self.total_cost_savings - self.ai_api_costs) / self.ai_api_costs) * 100
        return 0
    
    @classmethod
    def calculate_daily_metrics(cls, date=None):
        """ВИПРАВЛЕНИЙ розрахунок метрик за день з реалістичними обмеженнями"""
        if not date:
            date = timezone.now().date()
        
        # Отримуємо дані за день
        articles_today = ProcessedArticle.objects.filter(created_at__date=date)
        ai_logs_today = AIProcessingLog.objects.filter(created_at__date=date)
        social_posts_today = SocialMediaPost.objects.filter(created_at__date=date)
        
        # ВИПРАВЛЕНІ розрахунки з обмеженнями
        articles_count = min(articles_today.count(), 10)  # Max 10 articles/day
        ai_cost = min(float(ai_logs_today.aggregate(total=Sum('cost'))['total'] or 0), 50.0)  # Max $50/day
        processing_time = min(float(ai_logs_today.aggregate(total=Sum('processing_time'))['total'] or 0), 2.0)  # Max 2h/day
        
        # Кількість перекладів (статті * 3 мови)
        translations_made = min(articles_count * 3, 30)  # Max 30 translations/day
        
        # Кількість зображень
        images_generated = min(articles_today.filter(
            ai_image_url__isnull=False
        ).exclude(ai_image_url='').count(), 20)  # Max 20 images/day
        
        # Кількість соцмереж постів
        social_posts_generated = min(social_posts_today.count(), 15)  # Max 15 posts/day
        
        # Кількість автоматично призначених тегів
        tags_assigned = min(sum(article.tags.count() for article in articles_today), 50)  # Max 50 tags/day
        
        # Розраховуємо тегову аналітику
        tag_analytics = cls._calculate_tag_analytics(articles_today)
        
        # === РЕАЛІСТИЧНІ РОЗРАХУНКИ ===
        
        # Економія часу (3.5 години на статтю вручну)
        hours_per_article = 3.5
        manual_hours = articles_count * hours_per_article
        ai_hours = processing_time / 3600  # конвертуємо секунди в години
        time_saved = max(0, manual_hours - ai_hours)  # Не може бути негативним
        
        # Економія грошей (реалістичні ціни)
        cost_per_article_manual = 150.0  # $150 за статтю вручну
        total_savings = articles_count * cost_per_article_manual
        daily_operational_cost = 2.5  # $2.5 операційні витрати/день
        total_daily_cost = ai_cost + daily_operational_cost
        
        # Розподіл економії
        content_manager_cost = total_savings * 0.4  # 40% - контент менеджер
        smm_cost = total_savings * 0.2  # 20% - SMM
        copywriter_cost = total_savings * 0.4  # 40% - копірайтер
        
        # ROI розрахунок
        if total_daily_cost > 0:
            daily_roi = ((total_savings - total_daily_cost) / total_daily_cost) * 100
            daily_roi = max(-100, min(500, daily_roi))  # Обмежуємо -100% to +500%
        else:
            daily_roi = 0
        
        # Створюємо або оновлюємо запис
        roi, created = cls.objects.update_or_create(
            date=date,
            defaults={
                'manual_hours_saved': round(time_saved, 1),
                'ai_processing_time': round(ai_hours, 2),
                'time_efficiency': round((time_saved / manual_hours * 100) if manual_hours > 0 else 0, 1),
                'content_manager_cost_saved': round(content_manager_cost, 2),
                'smm_specialist_cost_saved': round(smm_cost, 2),
                'copywriter_cost_saved': round(copywriter_cost, 2),
                'ai_api_costs': round(ai_cost, 2),
                'net_savings': round(total_savings - total_daily_cost, 2),
                'articles_processed': articles_count,
                'translations_made': translations_made,
                'social_posts_generated': social_posts_generated,
                'images_generated': images_generated,
                'tags_assigned': tags_assigned,
                'avg_article_rating': 4.5,  # Фіксована оцінка
                'key_takeaways_en': [f"Processed {articles_count} articles with AI"],
                'key_takeaways_uk': [f"Оброблено {articles_count} статей з AI"],
                'key_takeaways_pl': [f"Przetworzono {articles_count} artykułów z AI"],
                'cross_promotion_success_rate': tag_analytics.get('cross_promotion_rate', 0),  # НОВИЙ
            }
        )
        
        return roi
    
    @classmethod
    def _calculate_article_rating(cls, articles_queryset):
        """Розраховує середню оцінку статей (0-6.0)"""
        if not articles_queryset.exists():
            return 0.0
        
        total_rating = 0
        count = 0
        
        for article in articles_queryset:
            # Базова оцінка
            rating = 3.0  # Середня база
            
            # +0.5 за високий пріоритет
            if article.priority >= 3:
                rating += 0.5
            
            # +0.5 за наявність AI зображення
            if article.ai_image_url:
                rating += 0.5
            
            # +1.0 за перегляди (якщо є)
            total_views = article.get_total_views()
            if total_views > 50:
                rating += 1.0
            elif total_views > 10:
                rating += 0.5
            
            # +0.5 за заповненість контенту
            if (article.business_insight_uk and 
                len(article.business_insight_uk) > 100):
                rating += 0.5
            
            # +0.5 за наявність тегів
            if article.tags.exists():
                rating += 0.5
            
            total_rating += min(rating, 6.0)  # Максимум 6.0
            count += 1
        
        return round(total_rating / count, 1) if count > 0 else 0.0
    
    @classmethod  
    def _generate_key_takeaways(cls, articles_queryset):
        """Генерує ключові висновки з оброблених статей"""
        if not articles_queryset.exists():
            return {
                'english': ['No articles processed today'],
                'ukrainian': ['Сьогодні статті не оброблялись'],
                'polish': ['Dzisiaj nie przetworzono artykułów']
            }
        
        # Топ категорії
        top_categories = articles_queryset.values(
            'category__name_uk', 'category__name_en', 'category__name_pl'
        ).annotate(count=Count('id')).order_by('-count')[:3]
        
        # AI моделі які використовувались
        ai_models = articles_queryset.values_list(
            'ai_model_used', flat=True
        ).distinct()
        
        # Топ теги
        top_tags = []
        for article in articles_queryset:
            top_tags.extend(article.tags.values_list('slug', flat=True))
        
        # Підраховуємо найпопулярніші теги
        from collections import Counter
        tag_counts = Counter(top_tags)
        most_common_tags = [tag for tag, count in tag_counts.most_common(3)]
        
        takeaways = {
            'english': [
                f"Processed {articles_queryset.count()} tech articles",
                f"Top category: {top_categories[0]['category__name_en'] if top_categories else 'General'}",
                f"AI models used: {', '.join(filter(None, ai_models))}",
                f"Popular tags: {', '.join(most_common_tags)}",
                "Multilingual content generated for EU market"
            ],
            'ukrainian': [
                f"Оброблено {articles_queryset.count()} технологічних статей",
                f"Топ категорія: {top_categories[0]['category__name_uk'] if top_categories else 'Загальне'}",
                f"Використано AI моделі: {', '.join(filter(None, ai_models))}",
                f"Популярні теги: {', '.join(most_common_tags)}",
                "Створено тримовний контент для ЄС ринку"
            ],
            'polish': [
                f"Przetworzono {articles_queryset.count()} artykułów technologicznych",
                f"Główna kategoria: {top_categories[0]['category__name_pl'] if top_categories else 'Ogólne'}",
                f"Używane modele AI: {', '.join(filter(None, ai_models))}",
                f"Popularne tagi: {', '.join(most_common_tags)}",
                "Wygenerowano treści w trzech językach dla rynku UE"
            ]
        }
        
        return takeaways
    
    @classmethod
    def _calculate_tag_analytics(cls, articles_queryset):
        """НОВИЙ: Розраховує аналітику тегів"""
        if not articles_queryset.exists():
            return {
                'top_tags': [],
                'engagement_stats': {},
                'cross_promotion_rate': 0
            }
        
        # Збираємо всі теги та їх метрики
        tag_stats = {}
        total_articles_with_tags = 0
        
        for article in articles_queryset:
            if article.tags.exists():
                total_articles_with_tags += 1
                article_views = article.get_total_views()
                
                for tag in article.tags.all():
                    if tag.slug not in tag_stats:
                        tag_stats[tag.slug] = {
                            'name': tag.get_name('uk'),
                            'articles_count': 0,
                            'total_views': 0,
                            'cross_promotion_potential': 0
                        }
                    
                    tag_stats[tag.slug]['articles_count'] += 1
                    tag_stats[tag.slug]['total_views'] += article_views
                    
                    # Рахуємо потенціал крос-промоції
                    related_projects = article.get_related_projects()
                    related_services = article.get_related_services()
                    if related_projects or related_services:
                        tag_stats[tag.slug]['cross_promotion_potential'] += 1
        
        # Топ теги за ефективністю
        top_tags = []
        for slug, stats in tag_stats.items():
            if stats['articles_count'] > 0:
                avg_views = stats['total_views'] / stats['articles_count']
                cross_promotion_rate = (stats['cross_promotion_potential'] / stats['articles_count']) * 100
                
                top_tags.append({
                    'slug': slug,
                    'name': stats['name'],
                    'articles_count': stats['articles_count'],
                    'avg_views_per_article': round(avg_views, 1),
                    'cross_promotion_rate': round(cross_promotion_rate, 1)
                })
        
        # Сортуємо за середніми переглядами
        top_tags.sort(key=lambda x: x['avg_views_per_article'], reverse=True)
        
        # Загальна успішність крос-промоції
        cross_promotion_success = 0
        if total_articles_with_tags > 0:
            articles_with_cross_promo = sum(
                1 for article in articles_queryset 
                if article.tags.exists() and (
                    article.get_related_projects() or article.get_related_services()
                )
            )
            cross_promotion_success = (articles_with_cross_promo / total_articles_with_tags) * 100
        
        return {
            'top_tags': top_tags[:5],  # Топ 5 тегів
            'engagement_stats': tag_stats,
            'cross_promotion_rate': round(cross_promotion_success, 1)
        }


class SocialMediaPost(models.Model):
    """Пости в соцмережах - для автопостингу"""
    
    PLATFORM_CHOICES = [
        ('telegram_uk', 'Telegram Ukraine'),
        ('instagram_pl', 'Instagram Poland'),
        ('facebook_pl', 'Facebook Poland'),
        ('instagram_en', 'Instagram English'),
        ('facebook_en', 'Facebook English'),
        ('linkedin_en', 'LinkedIn English'),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Чернетка')),
        ('scheduled', _('Заплановано')),
        ('published', _('Опубліковано')),
        ('failed', _('Помилка')),
    ]
    
    article = models.ForeignKey(ProcessedArticle, on_delete=models.CASCADE, related_name='social_posts')
    platform = models.CharField(_('Платформа'), max_length=20, choices=PLATFORM_CHOICES)
    
    # Контент поста
    content = models.TextField(_('Текст поста'))
    hashtags = models.CharField(_('Хештеги'), max_length=500, blank=True)
    image_url = models.URLField(_('Зображення'), blank=True)
    
    # Планування
    scheduled_at = models.DateTimeField(_('Заплановано на'), null=True, blank=True)
    published_at = models.DateTimeField(_('Опубліковано'), null=True, blank=True)
    
    # Статус та метрики
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='draft')
    external_post_id = models.CharField(_('ID в соцмережі'), max_length=100, blank=True)
    
    # Метрики (заповнюються автоматично)
    likes_count = models.IntegerField(_('Лайків'), default=0)
    comments_count = models.IntegerField(_('Коментарів'), default=0)
    shares_count = models.IntegerField(_('Поділились'), default=0)
    reach_count = models.IntegerField(_('Охоплення'), default=0)
    
    # Помилки
    error_message = models.TextField(_('Помилка'), blank=True)
    retry_count = models.IntegerField(_('Спроб публікації'), default=0)
    
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Пост в соцмережі')
        verbose_name_plural = _('Пости в соцмережах')
        ordering = ['-created_at']
        unique_together = ['article', 'platform']  # Один пост на платформу
    
    def __str__(self):
        return f"{self.get_platform_display()}: {self.content[:50]}..."
    
    @property
    def engagement_rate(self):
        """Коефіцієнт залучення"""
        if self.reach_count > 0:
            engagement = self.likes_count + self.comments_count + self.shares_count
            return (engagement / self.reach_count) * 100
        return 0
    
    def mark_as_published(self, external_id):
        """Позначити як опубліковано"""
        self.status = 'published'
        self.published_at = timezone.now()
        self.external_post_id = external_id
        self.save()


class NewsWidget(models.Model):
    """Налаштування віджета новин для головної сторінки"""
    
    WIDGET_TYPES = [
        ('latest', _('Останні новини')),
        ('trending', _('Популярні новини')),
        ('category', _('По категоріях')),
        ('featured', _('Рекомендовані')),
        ('top_articles', _('Топ статті')),  # НОВИЙ ТИП
    ]
    
    name = models.CharField(_('Назва віджета'), max_length=100)
    widget_type = models.CharField(_('Тип віджета'), max_length=20, choices=WIDGET_TYPES)
    
    # Налаштування відображення
    articles_limit = models.IntegerField(_('Кількість статей'), default=5)
    show_images = models.BooleanField(_('Показувати зображення'), default=True)
    show_date = models.BooleanField(_('Показувати дату'), default=True)
    show_category = models.BooleanField(_('Показувати категорію'), default=True)
    show_tags = models.BooleanField(_('Показувати теги'), default=False)  # НОВИЙ
    show_cross_promotion = models.BooleanField(_('Показувати крос-промоцію'), default=False)  # НОВИЙ
    
    # Фільтри
    categories = models.ManyToManyField(NewsCategory, blank=True, verbose_name=_('Категорії'))
    languages = models.JSONField(_('Мови'), default=list)  # ['en', 'uk', 'pl']
    
    # Стилізація
    css_class = models.CharField(_('CSS клас'), max_length=100, blank=True)
    background_color = models.CharField(_('Колір фону'), max_length=7, default='#ffffff')
    text_color = models.CharField(_('Колір тексту'), max_length=7, default='#333333')
    
    # Позиціонування
    position = models.IntegerField(_('Позиція на сторінці'), default=0)
    is_active = models.BooleanField(_('Активний'), default=True)
    
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Віджет новин')
        verbose_name_plural = _('Віджети новин')
        ordering = ['position']
    
    def __str__(self):
        return self.name
    
    def get_articles(self, language='uk'):
        """Отримує статті для віджета"""
        queryset = ProcessedArticle.objects.filter(status='published')
        
        # Фільтр по категоріях
        if self.categories.exists():
            queryset = queryset.filter(category__in=self.categories.all())
        
        # Сортування по типу
        if self.widget_type == 'latest':
            queryset = queryset.order_by('-published_at')
        elif self.widget_type == 'trending':
            # Сортуємо по переглядах за останній тиждень
            queryset = queryset.order_by('-views_count_uk', '-views_count_en', '-views_count_pl')
        elif self.widget_type == 'featured':
            queryset = queryset.filter(priority__gte=3).order_by('-priority', '-published_at')
        elif self.widget_type == 'top_articles':  # НОВИЙ ТИП
            queryset = queryset.filter(is_top_article=True).order_by('article_rank')
        
        return queryset[:self.articles_limit]


