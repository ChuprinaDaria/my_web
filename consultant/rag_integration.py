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
                # Метадата сесії для керування станом pricing
                meta = getattr(chat_session, 'metadata', {}) or {}
                awaiting = bool(meta.get('awaiting_pricing_details', False))
                completed = bool(meta.get('pricing_completed', False))

                # Використовуємо повноцінний RAG (усю режисуру робить services.py)
                result = self._generate_rag_response(user_message, chat_session)

                # Якщо намір не pricing — просто додамо консультаційні кнопки
                if result.get('intent') != 'pricing':
                    result.setdefault('actions', [])
                    result['actions'].extend([
                        {
                            'type': 'button',
                            'text': '📅 Записатися на консультацію (60 хв)',
                            'action': 'open_calendly',
                            'style': 'secondary',
                            'url': 'https://calendly.com/dchuprina-lazysoft/free-consultation-1h'
                        },
                        {
                            'type': 'button',
                            'text': '📅 Записатися на консультацію (30 хв)',
                            'action': 'open_calendly',
                            'style': 'secondary',
                            'url': 'https://calendly.com/dchuprina-lazysoft/30min'
                        }
                    ])
                
                # Гарантія наявності кнопки прорахунку при текстових ознаках цін
                content_text = (result.get('response') or '')
                text_lower = content_text.lower()
                has_textual_price = any(k in text_lower for k in ['орієнтовн', 'вартіст', 'price', 'usd']) or ('$' in content_text)
                final_prices_ready = bool(result.get('prices_ready')) or has_textual_price
                final_actions = list(result.get('actions', []) or [])
                has_quote_btn = any((a.get('type') == 'button' and a.get('action') == 'request_quote') for a in final_actions)
                if final_prices_ready and not has_quote_btn:
                    final_actions.append({
                        'type': 'button',
                        'text': '🧮 Отримати детальний прорахунок у PDF',
                        'action': 'request_quote',
                        'style': 'primary'
                    })

                processing_time = time.time() - start_time
                
                return {
                    'content': result['response'],
                    'intent': result.get('intent', 'general'),
                    'sources': result.get('sources', []),
                    'suggestions': result.get('suggestions', []),
                    'actions': final_actions,
                    'prices': result.get('prices', []),
                    'prices_ready': final_prices_ready,
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
        language = 'uk'
        try:
            lang_msg = chat_session.messages.filter(role='system', content__startswith='language:').order_by('created_at').last()
            if lang_msg and ':' in lang_msg.content:
                language = lang_msg.content.split(':', 1)[1].strip() or 'uk'
        except Exception:
            pass
        
        # Викликаємо RAG консультант
        result = self.rag_consultant.process_user_query(
            query=user_message,
            session_id=session_id,
            language=language
        )
        
        # Додаємо спеціальні дії для pricing (централізовано в RAGConsultantService)
        # Нічого не робимо тут, щоб уникнути дублювання логіки
        
        return result
    
    def _generate_pricing_actions(self, sources: List[Dict]) -> List[Dict]:
        """Генерує дії для ціноутворення"""
        actions = [
            {
                'type': 'button',
                'text': '🧮 Отримати прорахунок у PDF',
                'action': 'request_quote',
                'style': 'primary'
            },
            {
                'type': 'button',
                'text': '📅 Записатися на консультацію (60 хв)',
                'action': 'open_calendly',
                'style': 'secondary',
                'url': 'https://calendly.com/dchuprina-lazysoft/free-consultation-1h'
            },
            {
                'type': 'button',
                'text': '📅 Записатися на консультацію (30 хв)',
                'action': 'open_calendly',
                'style': 'secondary',
                'url': 'https://calendly.com/dchuprina-lazysoft/30min'
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
