from django.db import models
from django import forms 
from ckeditor.fields import RichTextField
from services.models import ServiceCategory
from django.utils.text import slugify  
from django.urls import reverse
from django.utils.translation import get_language


class Project(models.Model):
    slug = models.SlugField(max_length=255, unique=True)
    
    # Зв'язок з категорією сервісів
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='projects',
        null=False,
        blank=False,
        help_text="Категорія сервісу, до якої належить проєкт"
    )
    
    # 🏷️ НОВА СИСТЕМА ВНУТРІШНІХ ТЕГІВ для крос-промоції
    tags = models.ManyToManyField(
        'core.Tag',
        blank=True,
        related_name='projects',
        help_text="Внутрішні теги для крос-видачі з новинами та сервісами"
    )
    
    # Заголовки проєкту (багатомовність)
    title_en = models.CharField(max_length=255)
    title_uk = models.CharField(max_length=255)
    title_pl = models.CharField(max_length=255)
    
    # Короткий опис для карток
    short_description_en = RichTextField(blank=True, null=True, help_text="Короткий опис для відображення в картках")
    short_description_uk = RichTextField(blank=True, null=True)
    short_description_pl = RichTextField(blank=True, null=True)

    # 🏷️ СТАРІ ВІЗУАЛЬНІ ТЕГИ (залишаємо для сумісності, але deprecated)
    # Тип проєкту (головний тег) - DEPRECATED: використовуй нову систему тегів
    project_type_en = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="DEPRECATED: Використовуй нову систему тегів. Fintech Automation, E-commerce, AI Chat Bot, тощо"
    )
    project_type_uk = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="DEPRECATED: Використовуй нову систему тегів. Фінтех автоматизація, Електронна комерція, ШІ чат-бот, тощо"
    )
    project_type_pl = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="DEPRECATED: Використовуй нову систему тегів"
    )
    
    # Спеціальні бейджі (булеві поля) - ЗАЛИШАЄМО для візуального відображення
    is_top_project = models.BooleanField(
        default=False, 
        help_text="Показувати золотий бейдж 'TOP'"
    )
    is_innovative = models.BooleanField(
        default=False, 
        help_text="Показувати синій бейдж 'INNOVATIVE'"
    )
    is_ai_powered = models.BooleanField(
        default=False, 
        help_text="Показувати фіолетовий бейдж 'AI POWERED'"
    )
    is_enterprise = models.BooleanField(
        default=False, 
        help_text="Показувати бейдж 'ENTERPRISE'"
    )
    is_complex = models.BooleanField(
        default=False, 
        help_text="Показувати бейдж 'COMPLEX'"
    )
    
    # Кастомний бейдж (багатомовний) - ЗАЛИШАЄМО
    custom_badge_en = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Кастомний бейдж (наприклад: EXCLUSIVE, PREMIUM, тощо)"
    )
    custom_badge_uk = models.CharField(max_length=50, blank=True, null=True)
    custom_badge_pl = models.CharField(max_length=50, blank=True, null=True)
    
    # Колір кастомного бейджа
    BADGE_COLOR_CHOICES = [
        ('green', 'Зелений 🟢'),
        ('blue', 'Синій 🔵'),
        ('purple', 'Фіолетовий 🟣'),
        ('orange', 'Помаранчевий 🟠'),
        ('red', 'Червоний 🔴'),
        ('gold', 'Золотий 🟡'),
        ('pink', 'Рожевий 🩷'),
        ('cyan', 'Бірюзовий 🔷'),
    ]
    custom_badge_color = models.CharField(
        max_length=20,
        choices=BADGE_COLOR_CHOICES,
        default='green',
        help_text="Колір для кастомного бейджа"
    )
    
    # Рівень складності проєкту (впливає на яскравість ефектів)
    COMPLEXITY_CHOICES = [
        (1, '⭐ Simple - Простий'),
        (2, '⭐⭐ Medium - Середній'),
        (3, '⭐⭐⭐ Complex - Складний'),
        (4, '⭐⭐⭐⭐ Enterprise - Корпоративний'),
        (5, '⭐⭐⭐⭐⭐ Cutting Edge - Передовий')
    ]
    complexity_level = models.PositiveIntegerField(
        choices=COMPLEXITY_CHOICES,
        default=2,
        help_text="Рівень складності проєкту (впливає на яскравість ефектів та свічення)"
    )
    
    # Пріоритет проєкту (для сортування та візуального виділення)
    PRIORITY_CHOICES = [
        (1, 'Низький'),
        (2, 'Звичайний'),
        (3, 'Високий'),
        (4, 'Критичний'),
        (5, 'Топ проєкт'),
    ]
    priority = models.PositiveIntegerField(
        choices=PRIORITY_CHOICES,
        default=2,
        help_text="Пріоритет проєкту (впливає на порядок та яскравість відображення)"
    )
    
    # Статус завершення проєкту
    PROJECT_STATUS_CHOICES = [
        ('completed', '✅ Завершено'),
        ('ongoing', '🔄 В процесі'),
        ('maintenance', '🔧 Підтримка'),
        ('paused', '⏸️ Призупинено'),
        ('archived', '📦 Архівовано'),
    ]
    project_status = models.CharField(
        max_length=20,
        choices=PROJECT_STATUS_CHOICES,
        default='completed',
        help_text="Поточний статус проєкту"
    )
    
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

    client_request_extended_en = RichTextField(
        blank=True, 
        null=True,
        help_text="Детальний запит клієнта для сторінки проєкту (може містити скріншоти, діаграми)"
    )
    client_request_extended_uk = RichTextField(blank=True, null=True)
    client_request_extended_pl = RichTextField(blank=True, null=True)

    # Розширена реалізація (тільки для детальної сторінки)
    implementation_extended_en = RichTextField(
        blank=True, 
        null=True,
        help_text="Детальна реалізація з технічними деталями, архітектурою, процесом розробки"
    )
    implementation_extended_uk = RichTextField(blank=True, null=True)
    implementation_extended_pl = RichTextField(blank=True, null=True)

    # Розширені результати (тільки для детальної сторінки)
    results_extended_en = RichTextField(
        blank=True, 
        null=True,
        help_text="Детальні результати з метриками, графіками, статистикою"
    )
    results_extended_uk = RichTextField(blank=True, null=True)
    results_extended_pl = RichTextField(blank=True, null=True)

    # Виклики та рішення (нова секція)
    challenges_and_solutions_en = RichTextField(
        blank=True, 
        null=True,
        help_text="Які були виклики під час розробки і як їх вирішили"
    )
    challenges_and_solutions_uk = RichTextField(blank=True, null=True)
    challenges_and_solutions_pl = RichTextField(blank=True, null=True)

    # Уроки та висновки (нова секція)
    lessons_learned_en = RichTextField(
        blank=True, 
        null=True,
        help_text="Що вивчили під час проєкту, поради для майбутніх проєктів"
    )
    lessons_learned_uk = RichTextField(blank=True, null=True)
    lessons_learned_pl = RichTextField(blank=True, null=True)
    
    # Медіа файли для проєкту
    featured_image = models.ImageField(
        upload_to="projects/images/", 
        blank=True, 
        null=True,
        help_text="Основне зображення проєкту"
    )
    
    og_image = models.ImageField(
        upload_to='projects/og/', 
        null=True, blank=True,
        help_text="Зображення для соцмереж (1200x630px)"
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
    
    # 📊 МЕТРИКИ ПРОЄКТУ
    
    # Час виконання
    development_duration_weeks = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Скільки тижнів тривала розробка"
    )
    
    # Економія для клієнта
    client_time_saved_hours = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Скільки годин на тиждень економить клієнт"
    )
    
    # Бюджет проєкту (приблизний)
    BUDGET_RANGE_CHOICES = [
        ('small', '💰 $1k-5k'),
        ('medium', '💰💰 $5k-15k'),
        ('large', '💰💰💰 $15k-50k'),
        ('enterprise', '💰💰💰💰 $50k+'),
        ('custom', '🤝 Custom'),
    ]
    budget_range = models.CharField(
        max_length=20,
        choices=BUDGET_RANGE_CHOICES,
        blank=True,
        null=True,
        help_text="Приблизний діапазон бюджету проєкту"
    )
    
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
        ordering = ['-priority', '-order', '-project_date']
    
    def __str__(self):
        return self.title_en
    
    # 🛠️ НОВІ МЕТОДИ для крос-промоції з новою системою тегів
    
    def get_absolute_url(self, language: str = None):
        """Англійська без префікса, інші мови з префіксом, як у сервісах."""
        from django.utils.translation import get_language, override

        lang = (language or get_language() or 'en').lower()
        # Не додаємо `/{lang}` вручну — `reverse()` вже враховує `i18n_patterns`.
        with override(lang):
            return reverse('project_detail', kwargs={'slug': self.slug})

    def get_related_articles(self, limit=3):
        """Повертає новини: спочатку по категорії, потім по тегах"""
        try:
            from news.models import ProcessedArticle
            from django.db.models import Q
            
            qs = ProcessedArticle.objects.filter(status='published')
            
            # Спочатку новини з тієї ж категорії (якщо є мапа)
            by_cat = qs.none()  # Поки що немає мапи категорій новин ↔ сервіс-категорій
            
            # Потім новини з такими ж тегами
            by_tags = qs.filter(tags__in=self.tags.all()) if self.tags.exists() else qs.none()
            
            # Об'єднуємо результати
            return by_cat.union(by_tags).distinct().order_by('-published_at')[:limit]
        except ImportError:
            return []
    
    def get_related_services(self, limit=3):
        """Повертає сервіси: спочатку по категорії, потім по тегах"""
        try:
            from services.models import ServiceCategory
            from django.db.models import Q
            
            base_qs = ServiceCategory.objects.all()
            
            # Спочатку сервіси з тієї ж категорії (сам проєкт вже в цій категорії)
            by_cat = base_qs.filter(id=self.category.id)
            
            # Потім сервіси з такими ж тегами
            by_tags = base_qs.filter(tags__in=self.tags.all()) if self.tags.exists() else base_qs.none()
            
            # Об'єднуємо результати
            combined = by_cat.union(by_tags)
            return combined.order_by('-priority', '-date_created')[:limit]
        except ImportError:
            return []
    
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
        
        # Додаємо пов'язані сервіси  
        related_services = self.get_related_services(limit=3)
        for service in related_services:
            content.append({
                'type': 'service',
                'title': service.get_title('uk'),
                'summary': service.get_description('uk')[:150] + '...' if service.get_description('uk') else 'Детальний опис сервісу...',
                'url': f'/services/{service.slug}/',
                'image': service.icon.url if service.icon else None,
                'object': service
            })
        
        # Сортуємо за важливістю/датою
        content.sort(key=lambda x: x.get('date', x['object'].date_created), reverse=True)
        return content[:limit]
    
    def get_tag_names(self, language='uk'):
        """Повертає назви тегів для відображення"""
        return [tag.get_name(language) for tag in self.tags.filter(is_active=True)]
    
    def get_main_tags(self, limit=3):
        """Повертає основні теги проєкту для відображення в картках"""
        return self.tags.filter(is_active=True)[:limit]
    
    def auto_assign_tags_from_legacy(self):
        """
        🤖 АВТОМАТИЧНЕ призначення нових тегів на основі старих полів
        Викликається в data migration або management command
        """
        tags_to_assign = []
        
        # Аналізуємо старі поля та призначаємо відповідні теги
        if self.is_ai_powered:
            tags_to_assign.append('ai_ml')
        
        if 'automation' in (self.project_type_en or '').lower():
            tags_to_assign.append('process_automation')
        
        if 'chatbot' in (self.project_type_en or '').lower() or 'chat bot' in (self.project_type_en or '').lower():
            tags_to_assign.append('chatbots')
        
        if self.is_enterprise or 'enterprise' in (self.project_type_en or '').lower():
            tags_to_assign.append('business_optimization')
        
        if 'digital' in (self.project_type_en or '').lower() or 'transformation' in (self.project_type_en or '').lower():
            tags_to_assign.append('digital_transformation')
        
        if 'development' in (self.project_type_en or '').lower() or 'software' in (self.project_type_en or '').lower():
            tags_to_assign.append('software_development')
        
        # Призначаємо теги
        try:
            from core.models import Tag
            for tag_key in tags_to_assign:
                tag = Tag.objects.filter(slug=tag_key, is_active=True).first()
                if tag:
                    self.tags.add(tag)
        except ImportError:
            pass
        
        return tags_to_assign
    
    # 🛠️ ЗАЛИШЕНІ СТАРІ МЕТОДИ для сумісності
    
    def get_technologies_list(self):
        """Повертає список технологій як масив"""
        if self.technologies_used:
            return [tech.strip() for tech in self.technologies_used.split(',')]
        return []
    
    def get_project_type(self, lang='uk'):
        """DEPRECATED: Повертає тип проєкту для поточної мови. Використовуй нову систему тегів"""
        return getattr(self, f'project_type_{lang}', self.project_type_en) or ''
    
    def get_custom_badge(self, lang='uk'):
        """Повертає кастомний бейдж для поточної мови"""
        return getattr(self, f'custom_badge_{lang}', self.custom_badge_en) or ''
    
    def get_complexity_display_uk(self):
        """Повертає назву складності українською"""
        complexity_map = {
            1: 'Простий',
            2: 'Середній', 
            3: 'Складний',
            4: 'Корпоративний',
            5: 'Передовий'
        }
        return complexity_map.get(self.complexity_level, 'Середній')
    
    def get_status_emoji(self):
        """Повертає emoji для статусу проєкту"""
        status_emojis = {
            'completed': '✅',
            'ongoing': '🔄',
            'maintenance': '🔧',
            'paused': '⏸️',
            'archived': '📦',
        }
        return status_emojis.get(self.project_status, '✅')
    
    def get_priority_level(self):
        """Повертає текстовий рівень пріоритету"""
        if self.priority >= 5:
            return 'top'
        elif self.priority >= 4:
            return 'critical'
        elif self.priority >= 3:
            return 'high'
        else:
            return 'normal'
    
    def get_glow_intensity(self):
        """Повертає інтенсивність свічення на основі складності та пріоритету"""
        base_intensity = self.complexity_level * 0.2
        priority_bonus = self.priority * 0.1
        return min(base_intensity + priority_bonus, 1.0)  # Максимум 1.0
    
    def has_special_badges(self):
        """Перевіряє чи є спеціальні бейджі"""
        return (self.is_top_project or self.is_innovative or 
                self.is_ai_powered or self.is_enterprise or 
                self.is_complex or self.get_custom_badge())
    
    def get_all_badges(self, lang='uk'):
        """
        Повертає всі активні бейджі проєкту
        ОНОВЛЕНО: тепер включає нові теги + старі візуальні бейджі
        """
        badges = []
        
        # НОВІ ТЕГИ (пріоритетні)
        for tag in self.tags.filter(is_active=True):
            badges.append({
                'type': 'tag',
                'text': tag.get_name(lang),
                'icon': getattr(tag, 'icon', '️'),
                'color': tag.color,
                'key': getattr(tag, 'slug', None)
            })
        
        # СТАРІ ВІЗУАЛЬНІ БЕЙДЖІ (fallback для сумісності)
        if self.get_project_type(lang) and not self.tags.exists():
            badges.append({
                'type': 'primary',
                'text': self.get_project_type(lang),
                'icon': '🏢'
            })
        
        if self.is_top_project:
            badges.append({
                'type': 'top',
                'text': 'ТОП' if lang == 'uk' else 'TOP',
                'icon': '👑'
            })
        
        if self.is_innovative:
            badges.append({
                'type': 'innovation',
                'text': 'ІННОВАЦІЙНИЙ' if lang == 'uk' else 'INNOVATIVE',
                'icon': '⚡'
            })
        
        if self.is_ai_powered:
            badges.append({
                'type': 'ai',
                'text': 'ШІ ТЕХНОЛОГІЇ' if lang == 'uk' else 'AI POWERED',
                'icon': '🤖'
            })
        
        if self.is_enterprise:
            badges.append({
                'type': 'enterprise',
                'text': 'КОРПОРАТИВНИЙ' if lang == 'uk' else 'ENTERPRISE',
                'icon': '🏭'
            })
        
        if self.is_complex:
            badges.append({
                'type': 'complex',
                'text': 'СКЛАДНИЙ' if lang == 'uk' else 'COMPLEX',
                'icon': '🧩'
            })
        
        if self.get_custom_badge(lang):
            badges.append({
                'type': 'custom',
                'text': self.get_custom_badge(lang),
                'icon': '✨',
                'color': self.custom_badge_color
            })
        
        return badges


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