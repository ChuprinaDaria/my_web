from django.db import models
from django.utils import timezone
from .models import ChatSession, ChatMessage, KnowledgeSource, EmbeddingModel
from .services import EmbeddingService, IndexingService
import logging

logger = logging.getLogger(__name__)


class LearningPattern(models.Model):
    """Виявлені паттерни в діалогах для навчання"""
    
    # Паттерн запиту
    user_query_pattern = models.TextField(help_text="Типовий запит користувача")
    query_variations = models.JSONField(default=list, help_text="Варіації запиту")
    
    # Найкраща відповідь
    best_response = models.TextField(help_text="Найкраща відповідь на цей паттерн")
    response_source = models.CharField(
        max_length=50,
        choices=[
            ('human_feedback', 'Позитивний відгук користувача'),
            ('successful_conversion', 'Призвела до конверсії'),
            ('manual_approval', 'Схвалена вручну'),
            ('high_similarity', 'Висока схожість з існуючими знаннями'),
        ]
    )
    
    # Метрики
    frequency = models.PositiveIntegerField(default=1, help_text="Скільки разів зустрічався")
    success_rate = models.FloatField(default=0.0, help_text="Відсоток успішних відповідей")
    avg_user_satisfaction = models.FloatField(null=True, blank=True)
    
    # Статус навчання
    STATUS_CHOICES = [
        ('detected', 'Виявлено'),
        ('pending_review', 'Очікує перевірки'),
        ('approved', 'Схвалено'),
        ('indexed', 'Додано до бази знань'),
        ('rejected', 'Відхилено'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    
    # Категоризація
    detected_intent = models.CharField(max_length=50, blank=True)
    related_service_categories = models.JSONField(default=list)
    keywords = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Паттерн навчання"
        verbose_name_plural = "Паттерни навчання"
        ordering = ['-frequency', '-success_rate', '-created_at']
    
    def __str__(self):
        return f"{self.user_query_pattern[:50]}... ({self.frequency}x, {self.success_rate:.1%})"


class DialogAnalyzer:
    """Аналізує діалоги для виявлення паттернів"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.indexing_service = IndexingService()
    
    def analyze_recent_conversations(self, days=7):
        """Аналізує діалоги за останні дні"""
        from datetime import timedelta
        
        since_date = timezone.now() - timedelta(days=days)
        sessions = ChatSession.objects.filter(updated_at__gte=since_date)
        
        logger.info(f"Аналізуємо {sessions.count()} сесій за останні {days} днів")
        
        patterns_found = 0
        
        for session in sessions:
            try:
                patterns = self._analyze_session(session)
                patterns_found += len(patterns)
            except Exception as e:
                logger.error(f"Помилка аналізу сесії {session.id}: {e}")
        
        logger.info(f"Знайдено {patterns_found} нових паттернів")
        return patterns_found
    
    def _analyze_session(self, session):
        """Аналізує одну сесію"""
        messages = session.messages.order_by('created_at')
        patterns = []
        
        user_messages = [m for m in messages if m.role == 'user']
        assistant_messages = [m for m in messages if m.role == 'assistant']
        
        # Аналізуємо пари запит-відповідь
        for i, user_msg in enumerate(user_messages):
            # Шукаємо відповідну відповідь асистента
            assistant_response = None
            for assistant_msg in assistant_messages:
                if assistant_msg.created_at > user_msg.created_at:
                    assistant_response = assistant_msg
                    break
            
            if assistant_response:
                pattern = self._extract_pattern(
                    user_msg, 
                    assistant_response, 
                    session
                )
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    def _extract_pattern(self, user_msg, assistant_msg, session):
        """Витягує паттерн з пари повідомлень"""
        
        # Перевіряємо чи варто цей паттерн зберегти
        if not self._is_worth_learning(user_msg, assistant_msg, session):
            return None
        
        # Визначаємо намір та ключові слова
        detected_intent = self._detect_intent(user_msg.content)
        keywords = self._extract_keywords(user_msg.content)
        
        # Перевіряємо чи є схожий паттерн
        existing_pattern = self._find_similar_pattern(user_msg.content)
        
        if existing_pattern:
            # Оновлюємо існуючий
            existing_pattern.frequency += 1
            existing_pattern.query_variations = list(set(
                existing_pattern.query_variations + [user_msg.content]
            ))
            existing_pattern.save()
            return existing_pattern
        else:
            # Створюємо новий
            pattern = LearningPattern.objects.create(
                user_query_pattern=user_msg.content,
                query_variations=[user_msg.content],
                best_response=assistant_msg.content,
                response_source=self._determine_response_source(session),
                detected_intent=detected_intent,
                keywords=keywords,
                status='pending_review'
            )
            
            logger.info(f"Новий паттерн: {pattern.user_query_pattern[:50]}...")
            return pattern
    
    def _is_worth_learning(self, user_msg, assistant_msg, session):
        """Визначає чи варто вчитися на цьому діалозі"""
        
        # Не вчимося на дуже коротких повідомленнях
        if len(user_msg.content) < 10 or len(assistant_msg.content) < 20:
            return False
        
        # Не вчимося на помилках
        if "помилка" in assistant_msg.content.lower() or "error" in assistant_msg.content.lower():
            return False
        
        # Перевіряємо чи була позитивна реакція
        analytics = getattr(session, 'analytics', None)
        if analytics and hasattr(analytics, 'satisfaction_rating'):
            if analytics.satisfaction_rating and analytics.satisfaction_rating < 3:
                return False
        
        # Перевіряємо чи призвело до конверсії
        if getattr(session, 'lead_generated', False) or getattr(session, 'quote_requested', False):
            return True
        
        return True
    
    def _detect_intent(self, text):
        """Визначає намір з тексту"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['ціна', 'скільки', 'коштує', 'бюджет']):
            return 'pricing'
        elif any(word in text_lower for word in ['проєкт', 'кейс', 'приклад']):
            return 'portfolio'
        elif any(word in text_lower for word in ['сервіс', 'послуга', 'що робите']):
            return 'services'
        elif any(word in text_lower for word in ['як', 'процес', 'етапи']):
            return 'process'
        
        return 'general'
    
    def _extract_keywords(self, text):
        """Витягує ключові слова"""
        # Спрощена версія - можна покращити з NLP
        import re
        
        # Видаляємо стоп-слова
        stop_words = {'і', 'та', 'але', 'або', 'як', 'що', 'на', 'в', 'з', 'для', 'до', 'від'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Повертаємо топ-5 найдовших слів
        return sorted(set(keywords), key=len, reverse=True)[:5]
    
    def _find_similar_pattern(self, query):
        """Шукає схожі паттерни"""
        try:
            # Генеруємо embedding для запиту
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Шукаємо схожі паттерни (спрощена версія)
            existing_patterns = LearningPattern.objects.all()
            
            for pattern in existing_patterns:
                # Проста перевірка на схожість за ключовими словами
                pattern_words = set(pattern.user_query_pattern.lower().split())
                query_words = set(query.lower().split())
                
                overlap = len(pattern_words & query_words)
                if overlap > 2:  # Якщо збігається 3+ слова
                    return pattern
            
            return None
            
        except Exception as e:
            logger.error(f"Помилка пошуку схожих паттернів: {e}")
            return None
    
    def _determine_response_source(self, session):
        """Визначає джерело відповіді"""
        if getattr(session, 'lead_generated', False):
            return 'successful_conversion'
        
        analytics = getattr(session, 'analytics', None)
        if analytics and hasattr(analytics, 'satisfaction_rating'):
            if analytics.satisfaction_rating and analytics.satisfaction_rating >= 4:
                return 'human_feedback'
        
        return 'high_similarity'
    
    def approve_patterns_for_indexing(self, pattern_ids):
        """Схвалює паттерни для додавання до бази знань"""
        patterns = LearningPattern.objects.filter(
            id__in=pattern_ids,
            status='pending_review'
        )
        
        for pattern in patterns:
            try:
                # Створюємо KnowledgeSource
                knowledge = KnowledgeSource.objects.create(
                    title=f"Q&A: {pattern.user_query_pattern[:50]}...",
                    source_type='manual',
                    content_uk=f"Питання: {pattern.user_query_pattern}\n\nВідповідь: {pattern.best_response}",
                    tags=pattern.keywords,
                    priority=min(10 - pattern.frequency, 1),  # Чим частіше - тим вища пріоритет
                    auto_update=True
                )
                
                # Індексуємо
                self.indexing_service.reindex_object(knowledge)
                
                # Оновлюємо статус
                pattern.status = 'indexed'
                pattern.save()
                
                logger.info(f"Паттерн додано до бази знань: {pattern.id}")
                
            except Exception as e:
                logger.error(f"Помилка індексації паттерна {pattern.id}: {e}")
                pattern.status = 'rejected'
                pattern.save()


# Management команда для запуску аналізу
class LearningCommand:
    """Команда для запуску навчання"""
    
    @staticmethod
    def analyze_and_learn():
        analyzer = DialogAnalyzer()
        patterns_found = analyzer.analyze_recent_conversations(days=7)
        
        # Можна додати автоматичне схвалення найкращих паттернів
        high_quality_patterns = LearningPattern.objects.filter(
            status='pending_review',
            frequency__gte=3,  # Зустрічався 3+ рази
            success_rate__gte=0.8  # 80%+ успіх
        )[:10]  # Топ 10
        
        if high_quality_patterns:
            analyzer.approve_patterns_for_indexing(
                [p.id for p in high_quality_patterns]
            )
            
        return patterns_found
