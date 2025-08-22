from django.db import models
from ckeditor.fields import RichTextField
from django.utils.translation import get_language

class Contact(models.Model):
    """Контактна інформація компанії"""
    
    # Основна інформація
    title_en = models.CharField(max_length=255, default="Contact Us")
    title_uk = models.CharField(max_length=255, default="Зв'язатися з нами")
    title_pl = models.CharField(max_length=255, default="Skontaktuj się z nami")
    
    # Опис
    description_en = RichTextField(blank=True, null=True)
    description_uk = RichTextField(blank=True, null=True)
    description_pl = RichTextField(blank=True, null=True)
    
    # Контактні дані
    email = models.EmailField(default="hello@lazysoft.dev")
    phone = models.CharField(max_length=50, default="+48 727 842 737")
    
    # Адреса (СПРОЩЕНА)
    address_line_1_en = models.CharField(max_length=255, default="EU R&D Centre")
    address_line_1_uk = models.CharField(max_length=255, default="Центр досліджень ЄС")
    address_line_1_pl = models.CharField(max_length=255, default="Centrum Badawcze UE")
    
    # ВИДАЛЯЄМО address_line_2 та address_line_3
    city = models.CharField(max_length=100, default="Wrocław")
    postal_code = models.CharField(max_length=20, default="51-664")
    country_en = models.CharField(max_length=100, default="Poland")
    country_uk = models.CharField(max_length=100, default="Польща") 
    country_pl = models.CharField(max_length=100, default="Polska")
    
    # Google Maps
    google_maps_url = models.URLField(
        blank=True, 
        null=True,
        default="https://maps.google.com/maps?q=Wrocław,+Poland",
        help_text="Посилання на Google Maps"
    )
    
    # Фото офісу (основне)
    office_photo = models.ImageField(upload_to="contacts/office/", blank=True, null=True)
    
    # Текст для Hero фото секції
    hero_title_en = models.CharField(max_length=255, default="Our Space for Innovation")
    hero_title_uk = models.CharField(max_length=255, default="Наш простір для інновацій")
    hero_title_pl = models.CharField(max_length=255, default="Nasza przestrzeń do innowacji")
    
    hero_description_en = models.TextField(default="Modern office where ideas are born and the most ambitious projects come to life. Here we create the future together with our clients.")
    hero_description_uk = models.TextField(default="Сучасний офіс, де народжуються ідеї та втілюються найсміливіші проєкти. Тут ми створюємо майбутнє разом з нашими клієнтами.")
    hero_description_pl = models.TextField(default="Nowoczesne biuro, gdzie rodzą się pomysły i realizowane są najbardziej śmiałe projekty. Tutaj tworzymy przyszłość razem z naszymi klientami.")



    # Додаткове головне фото для Hero секції
    hero_photo = models.ImageField(
        upload_to="contacts/hero/", 
        blank=True, 
        null=True,
        help_text="Головне фото для Hero секції"
    )
    
    # Статус
    is_active = models.BooleanField(default=True)
    
    # SEO
    seo_title_en = models.CharField(max_length=255, blank=True)
    seo_title_uk = models.CharField(max_length=255, blank=True)
    seo_title_pl = models.CharField(max_length=255, blank=True)
    
    seo_description_en = models.TextField(max_length=300, blank=True)
    seo_description_uk = models.TextField(max_length=300, blank=True)
    seo_description_pl = models.TextField(max_length=300, blank=True)
    
    class Meta:
        verbose_name = "Contact Information"
        verbose_name_plural = "Contact Information"
    
    def __str__(self):
        return f"Contact Info ({self.email})"
    
    # 🔧 МЕТОДИ ДЛЯ БАГАТОМОВНОСТІ
    def get_title(self):
        """Отримати заголовок згідно поточної мови"""
        lang = get_language()
        if lang == 'uk':
            return self.title_uk
        elif lang == 'pl':
            return self.title_pl
        else:
            return self.title_en
    
    def get_description(self):
        """Отримати опис згідно поточної мови"""
        lang = get_language()
        if lang == 'uk':
            return self.description_uk
        elif lang == 'pl':
            return self.description_pl
        else:
            return self.description_en
    
    def get_address_line_1(self):
        """Отримати першу лінію адреси згідно поточної мови"""
        lang = get_language()
        if lang == 'uk':
            return self.address_line_1_uk
        elif lang == 'pl':
            return self.address_line_1_pl
        else:
            return self.address_line_1_en
    
    def get_country(self):
        """Отримати країну згідно поточної мови"""
        lang = get_language()
        if lang == 'uk':
            return self.country_uk
        elif lang == 'pl':
            return self.country_pl
        else:
            return self.country_en
    
    def get_country_code(self):
        """Отримати код країни"""
        return "PL"  # Тепер завжди Польща
    
    def get_seo_title(self):
        """SEO заголовок"""
        lang = get_language()
        if lang == 'uk':
            return self.seo_title_uk or self.title_uk
        elif lang == 'pl':
            return self.seo_title_pl or self.title_pl
        else:
            return self.seo_title_en or self.title_en
    
    def get_seo_description(self):
        """SEO опис"""
        lang = get_language()
        if lang == 'uk':
            return self.seo_description_uk
        elif lang == 'pl':
            return self.seo_description_pl
        else:
            return self.seo_description_en


class ContactSubmission(models.Model):
    """Форма зворотного зв'язку"""
    
    # Дані відправника
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    # З якої сторінки прийшов
    referred_from = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Наприклад: service_ai_automation, project_chatbot_analytics"
    )
    
    # Мета дані
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Статус обробки  
    is_processed = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Contact from {self.name} - {self.subject}"