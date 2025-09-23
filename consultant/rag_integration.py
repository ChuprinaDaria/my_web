import time
import logging
from typing import Dict, List
from django.conf import settings
from .models import ChatSession, ConsultantProfile, KnowledgeBase

# Імпортуємо мої RAG сервіси
try:
    from rag.services import RAGConsultantService, VectorSearchService, EmbeddingService
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedRAGConsultant:
    """Інтегрований RAG консультант для існуючого чату"""
    
    def __init__(self):
        self.rag_available = RAG_AVAILABLE
        
        if self.rag_available:
            self.rag_consultant = RAGConsultantService()
            self.vector_search = VectorSearchService()
        
        # Fallback до існуючої KnowledgeBase
        self.fallback_enabled = True
    
    def generate_response(self, user_message: str, chat_session: ChatSession) -> Dict:
        """Генерує відповідь через RAG або fallback"""
        
        start_time = time.time()
        
        if self.rag_available:
            try:
                # Використовуємо повноцінний RAG
                result = self._generate_rag_response(user_message, chat_session)
                
                processing_time = time.time() - start_time
                
                return {
                    'content': result['response'],
                    'intent': result.get('intent', 'general'),
                    'sources': result.get('sources', []),
                    'suggestions': result.get('suggestions', []),
                    'actions': result.get('actions', []),
                    'processing_time': processing_time,
                    'method': 'rag',
                    'tokens_used': len(result['response'].split()),
                }
                
            except Exception as e:
                logger.error(f"RAG помилка: {e}")
                # Fallback до простого алгоритму
        
        # Простий fallback алгоритм 
        if self.fallback_enabled:
            result = self._generate_fallback_response(user_message, chat_session)
            processing_time = time.time() - start_time
            
            return {
                'content': result,
                'intent': 'general',
                'sources': [],
                'suggestions': [],
                'actions': [],
                'processing_time': processing_time,
                'method': 'fallback',
                'tokens_used': len(result.split()),
            }
        
        return {
            'content': "Вибачте, зараз я не можу обробити ваш запит. Спробуйте пізніше.",
            'intent': 'error',
            'sources': [],
            'suggestions': [],
            'actions': [],
            'processing_time': time.time() - start_time,
            'method': 'error',
            'tokens_used': 0,
        }
    
    def _generate_rag_response(self, user_message: str, chat_session: ChatSession) -> Dict:
        """Генерує відповідь через повноцінний RAG"""
        
        # Конвертуємо session_id в строку для RAG
        session_id = str(chat_session.session_id)
        
        # Отримуємо мову (можна додати логіку визначення)
        language = 'uk'  # TODO: визначати з контексту або налаштувань
        
        # Викликаємо RAG консультант
        result = self.rag_consultant.process_user_query(
            query=user_message,
            session_id=session_id,
            language=language
        )
        
        # Додаємо спеціальні дії для pricing
        if result['intent'] == 'pricing':
            result['actions'] = self._generate_pricing_actions(result.get('sources', []))
        
        return result
    
    def _generate_pricing_actions(self, sources: List[Dict]) -> List[Dict]:
        """Генерує дії для ціноутворення"""
        actions = [
            {
                'type': 'button',
                'text': '🧮 Отримати прорахунок',
                'action': 'request_quote',
                'style': 'primary'
            },
            {
                'type': 'button',
                'text': '📅 Консультація',
                'action': 'schedule_consultation', 
                'style': 'secondary'
            }
        ]
        
        # Додаємо посилання на схожі проєкти
        if sources:
            for source in sources[:2]:
                if hasattr(source.get('object'), 'slug'):
                    obj = source['object']
                    if hasattr(obj, 'get_absolute_url'):
                        actions.append({
                            'type': 'link',
                            'text': f'📄 {source["content_title"][:30]}...',
                            'url': obj.get_absolute_url(),
                            'style': 'info'
                        })
        
        return actions
    
    def _generate_fallback_response(self, user_message: str, chat_session: ChatSession) -> str:
        """Fallback до простого алгоритму (існуючий код)"""
        
        import random
        
        # Використовуємо існуючу KnowledgeBase
        knowledge_items = KnowledgeBase.objects.filter(is_active=True).order_by('-priority')
        
        # Пошук релевантних знань (простий)
        relevant_knowledge = []
        user_words = user_message.lower().split()
        
        for item in knowledge_items:
            item_words = (item.title + ' ' + item.content).lower().split()
            if any(word in item_words for word in user_words):
                relevant_knowledge.append(item)
        
        # Базові відповіді
        responses = [
            f"Дякую за ваше питання! Це цікава тема.",
            "Я розумію ваш запит. Дозвольте мені допомогти вам з цим.",
            "Це важливе питання. Ось що я можу вам запропонувати:",
            "Відмінно! Давайте розглянемо це детальніше.",
        ]
        
        # Формуємо відповідь
        response = random.choice(responses)
        
        if relevant_knowledge:
            response += f"\n\nЗгідно з моєю базою знань:\n"
            for item in relevant_knowledge[:2]:
                response += f"• {item.title}: {item.content[:200]}...\n"
        
        # Додаємо загальні поради
        general_advice = [
            "Якщо у вас є додаткові питання, не соромтеся запитати!",
            "Можу допомогти з більш детальним поясненням.", 
            "Чи є щось конкретне, що вас цікавить?",
            "Готовий продовжити нашу розмову!",
        ]
        
        response += f"\n\n{random.choice(general_advice)}"
        
        return response
    
    def detect_intent(self, user_message: str) -> str:
        """Визначає намір користувача (спрощена версія)"""
        message_lower = user_message.lower()
        
        # Ключові слова для різних намірів
        if any(word in message_lower for word in ['ціна', 'скільки', 'коштує', 'бюджет', 'price']):
            return 'pricing'
        elif any(word in message_lower for word in ['консультація', 'зустріч', 'поговорити']):
            return 'consultation'  
        elif any(word in message_lower for word in ['проєкт', 'портфоліо', 'кейс', 'приклад']):
            return 'portfolio'
        elif any(word in message_lower for word in ['сервіс', 'послуга', 'що робите']):
            return 'services'
        
        return 'general'


# Глобальний екземпляр для використання в views
enhanced_consultant = EnhancedRAGConsultant()
