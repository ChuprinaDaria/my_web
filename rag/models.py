# rag/models.py
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from pgvector.django import VectorField
from django.utils import timezone
import json
from rag.utils import get_active_embedding_conf # Імпортуємо утиліту

# Отримуємо активну конфігурацію embeddings
ACTIVE_EMBEDDING_CONF = get_active_embedding_conf()
EMBEDDING_DIMENSIONS = ACTIVE_EMBEDDING_CONF["dim"]

class EmbeddingModel(models.Model):
    """Модель для зберігання векторних представлень контенту"""
    
    # Generic relation - може прив'язатися до будь-якої моделі
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Векторне представлення (розмірність з налаштувань)
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)  # Динамічна розмірність
    
    # Метадані для кращого пошуку
    content_text = models.TextField(help_text="Текст, з якого згенерований embedding")
    content_title = models.CharField(max_length=500, blank=True)
    content_category = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=5, default='uk')
    
    # Додаткові теги для фільтрування
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Технічна інфа
    model_name = models.CharField(max_length=50, default='gemini-text-embedding')
    embedding_version = models.CharField(max_length=20, default='1.0')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Векторне представлення"
        verbose_name_plural = "Векторні представлення"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['content_category', 'language']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        unique_together = ['content_type', 'object_id', 'language']
    
    def __str__(self):
        return f"{self.content_title[:50]} ({self.language})"


class ChatSession(models.Model):
    """Сесія чату з RAG консультантом"""
    
    session_id = models.CharField(max_length=100, unique=True)
    
    # Клієнт
    client_ip = models.GenericIPAddressField(blank=True, null=True)
    client_email = models.EmailField(blank=True)
    client_name = models.CharField(max_length=100, blank=True)
    
    # Динамічні метадані сесії (прапори, налаштування)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Мета розмови
    detected_intent = models.CharField(
        max_length=50,
        choices=[
            ('greeting', 'Привітання'),
            ('pricing', 'Питання про ціни'),
            ('services', 'Інфо про сервіси'),
            ('portfolio', 'Перегляд проєктів'),
            ('consultation', 'Запис на консультацію'),
            ('general', 'Загальні питання'),
        ],
        default='general'
    )
    
    detected_service_category = models.ForeignKey(
        'services.ServiceCategory',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="AI визначена категорія сервісу"
    )
    
    # Статистика
    total_messages = models.PositiveIntegerField(default=0)
    total_ai_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Результат
    lead_generated = models.BooleanField(default=False)
    quote_requested = models.BooleanField(default=False)
    consultation_requested = models.BooleanField(default=False)
    
    # Дати
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Чат сесія"
        verbose_name_plural = "Чат сесії"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Сесія {self.session_id} - {self.get_detected_intent_display()}"


class ChatMessage(models.Model):
    """Повідомлення в чаті"""
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    
    role = models.CharField(
        max_length=20,
        choices=[
            ('user', 'Користувач'),
            ('assistant', 'AI Консультант'),
            ('system', 'Система'),
        ]
    )
    
    content = models.TextField()
    
    # RAG метадані
    rag_sources_used = models.JSONField(default=list, blank=True, help_text="Список джерел для RAG відповіді")
    vector_search_results = models.JSONField(default=list, blank=True)
    ai_model_used = models.CharField(max_length=50, blank=True)
    processing_time = models.FloatField(null=True, blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Повідомлення чату"
        verbose_name_plural = "Повідомлення чатів"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."


class RAGAnalytics(models.Model):
    """Аналітика RAG системи"""
    
    date = models.DateField(default=timezone.now)
    
    # Статистика пошуків
    total_searches = models.PositiveIntegerField(default=0)
    successful_searches = models.PositiveIntegerField(default=0)  # Знайшли релевантні результати
    failed_searches = models.PositiveIntegerField(default=0)     # Нічого не знайшли
    
    # Популярні теми
    top_search_categories = models.JSONField(default=dict)  # {"web-development": 45, "ai": 23}
    top_search_queries = models.JSONField(default=list)    # ["скільки коштує сайт", "що таке AI"]
    
    # AI витрати
    total_ai_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    total_embeddings_generated = models.PositiveIntegerField(default=0)
    
    # Конверсії
    total_leads = models.PositiveIntegerField(default=0)
    total_quotes = models.PositiveIntegerField(default=0) 
    total_consultations = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Аналітика RAG"
        verbose_name_plural = "Аналітика RAG"
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Аналітика за {self.date}"


class KnowledgeSource(models.Model):
    """Джерела знань для RAG системи"""
    
    SOURCE_TYPES = [
        ('service', 'Сервіси'),
        ('project', 'Проєкти'),
        ('faq', 'FAQ'),
        ('manual', 'Ручний контент'),
    ]
    
    title = models.CharField(max_length=200)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    
    # Контент для індексації
    content_uk = models.TextField()
    content_en = models.TextField(blank=True)
    content_pl = models.TextField(blank=True)
    
    # Теги для кращого таргетингу
    tags = models.JSONField(default=list)
    priority = models.PositiveIntegerField(default=5, help_text="1=найвищий, 10=найнижчий")
    
    # Автоматичне оновлення
    auto_update = models.BooleanField(default=True, help_text="Автоматично оновлювати embeddings")
    last_embedding_update = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Джерело знань"
        verbose_name_plural = "Джерела знань"
        ordering = ['priority', '-updated_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_source_type_display()})"