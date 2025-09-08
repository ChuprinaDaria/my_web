from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class ChatSession(models.Model):
    """Модель для сесії чату з консультантом"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Сесія чату'
        verbose_name_plural = 'Сесії чату'
    
    def __str__(self):
        return f"Chat Session {self.session_id}"


class Message(models.Model):
    """Модель для повідомлень у чаті"""
    ROLE_CHOICES = [
        ('user', 'Користувач'),
        ('assistant', 'Консультант'),
        ('system', 'Система'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    processing_time = models.FloatField(null=True, blank=True)  # Час обробки в секундах
    tokens_used = models.IntegerField(null=True, blank=True)  # Кількість токенів
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ConsultantProfile(models.Model):
    """Профіль консультанта з налаштуваннями"""
    name = models.CharField(max_length=100, default="RAG Консультант")
    description = models.TextField(default="Штучний інтелект для консультацій та допомоги")
    avatar = models.CharField(max_length=10, default="🫧")
    is_active = models.BooleanField(default=True)
    max_tokens = models.IntegerField(default=4000)
    temperature = models.FloatField(default=0.7)
    system_prompt = models.TextField(
        default="Ти RAG консультант - штучний інтелект, який допомагає користувачам з різними питаннями. "
                "Відповідай корисними, точними та дружелюбними відповідями українською мовою."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Профіль консультанта'
        verbose_name_plural = 'Профілі консультанта'
    
    def __str__(self):
        return self.name


class KnowledgeBase(models.Model):
    """База знань для RAG консультанта"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=100, null=True, blank=True)
    tags = models.CharField(max_length=500, null=True, blank=True, help_text="Теги через кому")
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Пріоритет (вищий = важливіший)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = 'База знань'
        verbose_name_plural = 'База знань'
    
    def __str__(self):
        return self.title
    
    def get_tags_list(self):
        """Повертає список тегів"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []


class ChatAnalytics(models.Model):
    """Аналітика чату"""
    chat_session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name='analytics')
    total_messages = models.IntegerField(default=0)
    user_messages = models.IntegerField(default=0)
    assistant_messages = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    session_duration = models.FloatField(null=True, blank=True)  # Тривалість в секундах
    satisfaction_rating = models.IntegerField(null=True, blank=True, choices=[
        (1, 'Дуже погано'),
        (2, 'Погано'),
        (3, 'Нормально'),
        (4, 'Добре'),
        (5, 'Відмінно'),
    ])
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Аналітика чату'
        verbose_name_plural = 'Аналітика чатів'
    
    def __str__(self):
        return f"Analytics for {self.chat_session.session_id}"