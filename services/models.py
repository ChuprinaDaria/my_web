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

    short_description_en = models.TextField(blank=True, null=True)
    short_description_uk = models.TextField(blank=True, null=True)
    short_description_pl = models.TextField(blank=True, null=True)

    seo_title_en = models.CharField(max_length=255, blank=True, null=True)
    seo_title_uk = models.CharField(max_length=255, blank=True, null=True)
    seo_title_pl = models.CharField(max_length=255, blank=True, null=True)
    seo_description_en = models.TextField(blank=True, null=True)
    seo_description_uk = models.TextField(blank=True, null=True)
    seo_description_pl = models.TextField(blank=True, null=True)

    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to="services/videos/", blank=True, null=True)

    gallery_image_1 = models.ImageField(upload_to="services/gallery/", blank=True, null=True)
    gallery_image_2 = models.ImageField(upload_to="services/gallery/", blank=True, null=True)
    gallery_image_3 = models.ImageField(upload_to="services/gallery/", blank=True, null=True)
    gallery_image_4 = models.ImageField(upload_to="services/gallery/", blank=True, null=True)

    target_audience_en = RichTextField(blank=True, null=True)
    target_audience_uk = RichTextField(blank=True, null=True)
    target_audience_pl = RichTextField(blank=True, null=True)

    pricing_en = RichTextField(blank=True, null=True)
    pricing_uk = RichTextField(blank=True, null=True)
    pricing_pl = RichTextField(blank=True, null=True)

    value_proposition_en = RichTextField(blank=True, null=True)
    value_proposition_uk = RichTextField(blank=True, null=True)
    value_proposition_pl = RichTextField(blank=True, null=True)

    icon = models.ImageField(upload_to="services/icons/", blank=True, null=True)
    
    main_image = models.ImageField(
        upload_to='services/main/', 
        null=True, blank=True,
        verbose_name="Головне зображення",
        help_text="Рекомендований розмір: 400x250px"
    )
    
    cta_text_en = models.CharField(max_length=50, default="Learn More")
    cta_text_uk = models.CharField(max_length=50, default="Дізнатися більше") 
    cta_text_pl = models.CharField(max_length=50, default="Dowiedz się więcej")
    
    cta_url = models.URLField(blank=True, null=True, help_text="Посилання для CTA кнопки")
    
    is_featured = models.BooleanField(default=False)
    PRIORITY_CHOICES = [
        (1, 'Низький'),
        (2, 'Звичайний'),
        (3, 'Високий'),
        (4, 'Критичний'),
        (5, 'Топ сервіс')
    ]
    priority = models.PositiveIntegerField(choices=PRIORITY_CHOICES, default=2)
    order = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField('core.Tag', blank=True, related_name='service_categories')
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['-priority','-order','-date_created']
        indexes = [
            models.Index(fields=['is_featured', 'priority']),
            models.Index(fields=['slug']),
            models.Index(fields=['date_created']),
        ]

    def __str__(self):
        return self.title_en

    def get_title(self, lang='uk'):
        return getattr(self, f'title_{lang}', self.title_en)

    def get_desc(self, lang='uk'):
        return getattr(self, f'description_{lang}', None)

    def get_short(self, lang='uk'):
        return getattr(self, f'short_description_{lang}', None)

    def get_seo_title(self, lang='uk'):
        v = getattr(self, f'seo_title_{lang}', None)
        return v or self.get_title(lang)

    def get_seo_desc(self, lang='uk'):
        v = getattr(self, f'seo_description_{lang}', None)
        return v or (self.get_short(lang) or '')

    def get_audience(self, lang='uk'):
        return getattr(self, f'target_audience_{lang}', None)

    def get_pricing(self, lang='uk'):
        return getattr(self, f'pricing_{lang}', None)

    def get_value(self, lang='uk'):
        return getattr(self, f'value_proposition_{lang}', None)

    def get_priority_emoji(self):
        m = {1:'⚪',2:'🔵',3:'🟡',4:'🟠',5:'🔴'}
        return m.get(self.priority,'🔵')

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


class Service(models.Model):
    slug = models.SlugField(max_length=255, unique=True)

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='services',
        null=False,
        blank=False
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

    # 🏷️ НОВА СИСТЕМА ВНУТРІШНІХ ТЕГІВ для крос-промоції
    tags = models.ManyToManyField(
        'core.Tag',
        blank=True,
        related_name='services',
        help_text="Внутрішні теги для крос-видачі з новинами та проєктами"
    )

    # 📊 НОВІ поля для покращення функціональності
    PRIORITY_CHOICES = [
        (1, 'Низький'),
        (2, 'Звичайний'),
        (3, 'Високий'),
        (4, 'Критичний'),
        (5, 'Топ сервіс'),
    ]
    priority = models.PositiveIntegerField(
        choices=PRIORITY_CHOICES,
        default=2,
        help_text="Пріоритет сервісу для сортування"
    )

    is_featured = models.BooleanField(
        default=False, 
        help_text="Показувати на головній сторінці"
    )

    order = models.PositiveIntegerField(
        default=0, 
        help_text="Порядок відображення"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_uk)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['-priority', '-order', '-date_created']  # Оновлено сортування

    def __str__(self):
        return self.title_en

    # 🛠️ НОВІ методи для крос-промоції з новою системою тегів

    def get_related_articles(self, limit=3):
        """Повертає новини з такими ж тегами - ЗАВЖДИ QuerySet"""
        if self.tags.exists():
            try:
                from news.models import ProcessedArticle
                return ProcessedArticle.objects.filter(
                    tags__in=self.tags.all(),
                    status='published'
                ).distinct().order_by('-published_at')[:limit]
            except ImportError:
                # Повертаємо пустий QuerySet, а не список
                from django.db.models import QuerySet
                return ProcessedArticle.objects.none()
        
        # Тут також пустий QuerySet
        try:
            from news.models import ProcessedArticle
            return ProcessedArticle.objects.none()
        except ImportError:
            return Service.objects.none()  # або будь-який пустий QuerySet

    def get_related_projects(self, limit=3):
        """Повертає проєкти з такими ж тегами - ЗАВЖДИ QuerySet"""
        if self.tags.exists():
            try:
                from projects.models import Project
                return Project.objects.filter(
                    tags__in=self.tags.all(),
                    is_active=True
                ).distinct().order_by('-date_created')[:limit]
            except ImportError:
                try:
                    from projects.models import Project
                    return Project.objects.none()
                except ImportError:
                    return Service.objects.none()
        
        try:
            from projects.models import Project
            return Project.objects.none()
        except ImportError:
            return Service.objects.none()

    
    def get_cross_promotion_content(self, limit=6):
        """
        Повертає змішаний контент для крос-промоції
        Використовується в шаблонах для показу пов'язаного контенту
        """
        content = []

        # Додаємо пов'язані новини
        related_articles = self.get_related_articles(limit=3)
        for article in related_articles:
            content.append({
                'type': 'article',
                'title': article.get_title('uk'),
                'summary': article.get_summary('uk')[:150] + '...',
                'url': article.get_absolute_url(),
                'image': article.ai_image_url,
                'date': article.published_at,
                'source_domain': article.source_domain,
                'object': article
            })

        # Додаємо пов'язані проєкти
        related_projects = self.get_related_projects(limit=3)
        for project in related_projects:
            content.append({
                'type': 'project',
                'title': project.title_uk,
                'summary': getattr(project, 'short_description_uk', '') or 'Детальний опис проєкту...',
                'url': f'/projects/{project.slug}/',
                'image': project.featured_image.url if project.featured_image else None,
                'badges': project.get_all_badges('uk'),
                'object': project
            })

        # Сортуємо за датою
        content.sort(key=lambda x: x.get('date', x['object'].date_created), reverse=True)
        return content[:limit]

    def get_tag_names(self, language='uk'):
        """Повертає назви тегів для відображення"""
        return [tag.get_name(language) for tag in self.tags.filter(is_active=True)]

    def get_main_tags(self, limit=3):
        """Повертає основні теги сервісу для відображення в картках"""
        return self.tags.filter(is_active=True)[:limit]

    def auto_assign_tags_from_content(self):
        """
        🤖 АВТОМАТИЧНЕ призначення тегів на основі контенту сервісу
        Аналізує заголовки та описи для призначення відповідних тегів
        """
        tags_to_assign = []
        
        # Аналізуємо контент сервісу
        all_content = f"{self.title_en} {self.title_uk} {self.description_en} {self.description_uk}".lower()
        
        # Мапа ключових слів до тегів
        keyword_to_tag = {
            'ai_ml': ['ai', 'artificial intelligence', 'machine learning', 'штучний інтелект', 'машинне навчання', 'нейрон'],
            'process_automation': ['automation', 'автоматизація', 'automatic', 'workflow', 'робочий процес'],
            'chatbots': ['chatbot', 'chat bot', 'чат-бот', 'virtual assistant', 'віртуальний асистент'],
            'business_optimization': ['optimization', 'оптимізація', 'efficiency', 'ефективність', 'процес'],
            'digital_transformation': ['digital', 'цифровий', 'transformation', 'трансформація', 'digitalization'],
            'software_development': ['development', 'розробка', 'software', 'програмне забезпечення', 'api', 'integration']
        }
        
        # Перевіряємо які теги підходять
        for tag_key, keywords in keyword_to_tag.items():
            for keyword in keywords:
                if keyword in all_content:
                    tags_to_assign.append(tag_key)
                    break  # Достатньо одного збігу на тег
        
        # Призначаємо теги
        try:
            from core.models import Tag
            for tag_key in set(tags_to_assign):  # Видаляємо дублікати
                tag = Tag.objects.filter(slug=tag_key, is_active=True).first()
                if tag:
                    self.tags.add(tag)
        except ImportError:
            pass
        
        return tags_to_assign

    def get_priority_display(self):
        """Повертає текстовий рівень пріоритету"""
        if self.priority >= 5:
            return 'top'
        elif self.priority >= 4:
            return 'critical'
        elif self.priority >= 3:
            return 'high'
        else:
            return 'normal'

    def get_priority_emoji(self):
        """Повертає emoji для пріоритету"""
        priority_emojis = {
            1: '⚪',
            2: '🔵',
            3: '🟡',
            4: '🟠',
            5: '🔴',
        }
        return priority_emojis.get(self.priority, '🔵')

    # 🛠️ HELPER методи для багатомовності (додано для зручності)



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