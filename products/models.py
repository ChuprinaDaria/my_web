from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.urls import reverse
from django.utils.translation import get_language, override
from services.models import ServiceCategory


class Product(models.Model):
    """Модель для продуктів (наприклад, SLOTH AI)"""
    slug = models.SlugField(max_length=255, unique=True)

    # Зв'язок з сервісами
    related_services = models.ManyToManyField(
        ServiceCategory,
        blank=True,
        related_name='products',
        help_text="Пов'язані сервіси"
    )

    # Теги для крос-промоції
    tags = models.ManyToManyField(
        'core.Tag',
        blank=True,
        related_name='products',
        help_text="Внутрішні теги для крос-видачі з новинами та сервісами"
    )

    # Заголовки продукту (багатомовність)
    title_en = models.CharField(max_length=255)
    title_uk = models.CharField(max_length=255)
    title_pl = models.CharField(max_length=255)

    # Короткий опис для карток
    short_description_en = RichTextField(
        blank=True, null=True,
        help_text="Короткий опис для відображення в картках"
    )
    short_description_uk = RichTextField(blank=True, null=True)
    short_description_pl = RichTextField(blank=True, null=True)

    # Повний опис продукту
    description_en = RichTextField(help_text="Повний опис продукту")
    description_uk = RichTextField()
    description_pl = RichTextField()

    # Для кого цей продукт
    target_audience_en = RichTextField(
        blank=True, null=True,
        help_text="Для кого призначений продукт"
    )
    target_audience_uk = RichTextField(blank=True, null=True)
    target_audience_pl = RichTextField(blank=True, null=True)

    # Ключові можливості / Features
    features_en = RichTextField(
        blank=True, null=True,
        help_text="Ключові можливості продукту"
    )
    features_uk = RichTextField(blank=True, null=True)
    features_pl = RichTextField(blank=True, null=True)

    # Як це працює
    how_it_works_en = RichTextField(blank=True, null=True)
    how_it_works_uk = RichTextField(blank=True, null=True)
    how_it_works_pl = RichTextField(blank=True, null=True)

    # Медіа файли
    featured_image = models.ImageField(
        upload_to="products/images/",
        blank=True, null=True,
        help_text="Основне зображення продукту"
    )

    og_image = models.ImageField(
        upload_to='products/og/',
        null=True, blank=True,
        help_text="Зображення для соцмереж (1200x630px)"
    )

    icon = models.ImageField(
        upload_to="products/icons/",
        blank=True, null=True,
        help_text="Іконка продукту для карток"
    )

    gallery_image_1 = models.ImageField(upload_to="products/gallery/", blank=True, null=True)
    gallery_image_2 = models.ImageField(upload_to="products/gallery/", blank=True, null=True)
    gallery_image_3 = models.ImageField(upload_to="products/gallery/", blank=True, null=True)
    gallery_image_4 = models.ImageField(upload_to="products/gallery/", blank=True, null=True)

    # Відео
    video_url = models.URLField(
        blank=True, null=True,
        help_text="YouTube, Vimeo або інший URL"
    )
    video_file = models.FileField(
        upload_to="products/videos/",
        blank=True, null=True,
        help_text="Або завантажте відео файл"
    )

    # CTA - головна кнопка
    cta_text_en = models.CharField(
        max_length=100,
        default="Try Free Trial",
        help_text="Текст головної CTA кнопки"
    )
    cta_text_uk = models.CharField(
        max_length=100,
        default="Спробувати безкоштовно"
    )
    cta_text_pl = models.CharField(
        max_length=100,
        default="Wypróbuj za darmo"
    )

    cta_url = models.URLField(
        default="https://sloth-ai.lazysoft.pl",
        help_text="Посилання для головної CTA кнопки (наприклад, на trial)"
    )

    # SEO поля
    seo_title_en = models.CharField(max_length=255)
    seo_title_uk = models.CharField(max_length=255, blank=True, null=True)
    seo_title_pl = models.CharField(max_length=255, blank=True, null=True)

    seo_description_en = models.TextField(max_length=300)
    seo_description_uk = models.TextField(max_length=300, blank=True, null=True)
    seo_description_pl = models.TextField(max_length=300, blank=True, null=True)

    # Статус та пріоритет
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(
        default=True,
        help_text="Показувати на головній сторінці"
    )

    PRIORITY_CHOICES = [
        (1, 'Низький'),
        (2, 'Звичайний'),
        (3, 'Високий'),
        (4, 'Критичний'),
        (5, 'Топ продукт'),
    ]
    priority = models.PositiveIntegerField(
        choices=PRIORITY_CHOICES,
        default=5,
        help_text="Пріоритет продукту (впливає на порядок та яскравість відображення)"
    )

    order = models.PositiveIntegerField(default=0, help_text="Порядок відображення")

    # Дати
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    launch_date = models.DateField(
        null=True, blank=True,
        help_text="Дата запуску продукту"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_en)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-priority', '-order', '-date_created']

    def __str__(self):
        return self.title_en

    def get_absolute_url(self, language: str = None):
        """URL продукту з підтримкою мов. Англійська без /en/, uk/pl з префіксом."""
        lang = (language or get_language() or 'en').lower()
        with override(lang):
            return reverse('products:product_detail', kwargs={'slug': self.slug})

    def get_title(self, lang='uk'):
        return getattr(self, f'title_{lang}', self.title_en)

    def get_short_description(self, lang='uk'):
        return getattr(self, f'short_description_{lang}', None)

    def get_description(self, lang='uk'):
        return getattr(self, f'description_{lang}', None)

    def get_target_audience(self, lang='uk'):
        return getattr(self, f'target_audience_{lang}', None)

    def get_features(self, lang='uk'):
        return getattr(self, f'features_{lang}', None)

    def get_how_it_works(self, lang='uk'):
        return getattr(self, f'how_it_works_{lang}', None)

    def get_cta_text(self, lang='uk'):
        return getattr(self, f'cta_text_{lang}', self.cta_text_en)

    def get_seo_title(self, lang='uk'):
        v = getattr(self, f'seo_title_{lang}', None)
        return v or self.get_title(lang)

    def get_seo_description(self, lang='uk'):
        v = getattr(self, f'seo_description_{lang}', None)
        return v or ''

    def get_gallery_images(self):
        """Повертає всі галерейні зображення"""
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

    def get_related_articles(self, limit=3):
        """Повертає новини з такими ж тегами"""
        if self.tags.exists():
            try:
                from news.models import ProcessedArticle
                return ProcessedArticle.objects.filter(
                    tags__in=self.tags.all(),
                    status='published'
                ).distinct().order_by('-published_at')[:limit]
            except ImportError:
                pass
        return []

    def get_related_projects(self, limit=3):
        """Повертає проєкти пов'язані з цим продуктом"""
        try:
            from projects.models import Project
            # Проєкти з такими ж тегами або з пов'язаних сервісів
            projects = Project.objects.filter(
                models.Q(tags__in=self.tags.all()) |
                models.Q(category__in=self.related_services.all()),
                is_active=True
            ).distinct().order_by('-priority', '-date_created')[:limit]
            return projects
        except ImportError:
            return []


class ProductPricingPackage(models.Model):
    """Пакети з цінами для продукту"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='pricing_packages'
    )

    # Назва пакету
    name_en = models.CharField(max_length=100, help_text="Назва пакету (наприклад, Starter, Pro, Enterprise)")
    name_uk = models.CharField(max_length=100)
    name_pl = models.CharField(max_length=100)

    # Опис пакету
    description_en = RichTextField(blank=True, null=True)
    description_uk = RichTextField(blank=True, null=True)
    description_pl = RichTextField(blank=True, null=True)

    # Ціна
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Ціна пакету"
    )

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('PLN', 'Polish Zloty (zł)'),
        ('UAH', 'Ukrainian Hryvnia (₴)'),
    ]
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )

    BILLING_PERIOD_CHOICES = [
        ('month', 'Per Month'),
        ('year', 'Per Year'),
        ('one_time', 'One Time'),
        ('custom', 'Custom'),
    ]
    billing_period = models.CharField(
        max_length=20,
        choices=BILLING_PERIOD_CHOICES,
        default='month'
    )

    # Особливості пакету (можливості)
    features_en = RichTextField(
        blank=True, null=True,
        help_text="Список можливостей цього пакету"
    )
    features_uk = RichTextField(blank=True, null=True)
    features_pl = RichTextField(blank=True, null=True)

    # Чи є це рекомендованим пакетом
    is_recommended = models.BooleanField(
        default=False,
        help_text="Виділити цей пакет як рекомендований"
    )

    # Чи є trial
    has_trial = models.BooleanField(
        default=False,
        help_text="Чи доступний безкоштовний trial для цього пакету"
    )

    trial_days = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Кількість днів trial періоду"
    )

    # Порядок відображення
    order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Pricing Package"
        verbose_name_plural = "Pricing Packages"
        ordering = ['order', 'price']

    def __str__(self):
        return f"{self.product.title_en} - {self.name_en} (${self.price})"

    def get_name(self, lang='uk'):
        return getattr(self, f'name_{lang}', self.name_en)

    def get_description(self, lang='uk'):
        return getattr(self, f'description_{lang}', None)

    def get_features(self, lang='uk'):
        return getattr(self, f'features_{lang}', None)

    def get_price_display(self):
        """Форматована ціна з валютою"""
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'PLN': 'zł',
            'UAH': '₴',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.price}"

    def get_billing_period_display_translated(self, lang='uk'):
        """Переклад періоду оплати"""
        translations = {
            'month': {'en': 'per month', 'uk': 'на місяць', 'pl': 'na miesiąc'},
            'year': {'en': 'per year', 'uk': 'на рік', 'pl': 'na rok'},
            'one_time': {'en': 'one time', 'uk': 'одноразово', 'pl': 'jednorazowo'},
            'custom': {'en': 'custom', 'uk': 'індивідуально', 'pl': 'indywidualnie'},
        }
        return translations.get(self.billing_period, {}).get(lang, self.get_billing_period_display())


class ProductReview(models.Model):
    """Відгуки користувачів про продукт"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    # Інформація про автора відгуку
    author_name = models.CharField(max_length=255)
    author_position = models.CharField(max_length=255, blank=True, null=True)
    author_company = models.CharField(max_length=255, blank=True, null=True)
    author_avatar = models.ImageField(
        upload_to="products/reviews/",
        blank=True, null=True
    )

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
    is_featured = models.BooleanField(
        default=False,
        help_text="Показувати на головній сторінці продукту"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        ordering = ['-is_featured', '-rating', '-date_created']

    def __str__(self):
        return f"Review for {self.product.title_en} by {self.author_name}"

    def get_review_text(self, lang='uk'):
        return getattr(self, f'review_text_{lang}', self.review_text_en)
