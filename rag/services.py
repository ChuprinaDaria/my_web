# rag/services.py
import os
import json
import logging
from typing import List, Dict, Tuple, Optional
from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from pgvector.django import CosineDistance
import google.generativeai as genai
from openai import OpenAI
from django.utils import timezone

from .models import EmbeddingModel, ChatSession, ChatMessage, RAGAnalytics
from services.models import ServiceCategory, FAQ
from projects.models import Project
from pricing.models import ServicePricing

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Сервіс для генерації та управління embedding'ами"""
    
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        # Налаштування з settings
        self.rag_settings = getattr(settings, 'RAG_SETTINGS', {})
        self.embedding_model = self.rag_settings.get('EMBEDDING_MODEL', 'gemini')
        
        # Ініціалізація AI клієнтів
        if self.embedding_model == 'gemini' and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
    
    def generate_embedding(self, text: str, model: str = None) -> List[float]:
        """Генерує embedding для тексту"""
        if not text.strip():
            raise ValueError("Текст не може бути пустим")
            
        model = model or self.embedding_model
        
        try:
            if model == 'gemini':
                return self._generate_gemini_embedding(text)
            elif model == 'openai':
                return self._generate_openai_embedding(text)
            else:
                raise ValueError(f"Невідома модель: {model}")
                
        except Exception as e:
            logger.error(f"Помилка генерації embedding: {e}")
            raise
    
    def _generate_gemini_embedding(self, text: str) -> List[float]:
        """Генерація embedding через Gemini"""
        model = self.rag_settings.get('GEMINI_EMBEDDING_MODEL', 'models/embedding-001')
        
        response = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document"
        )
        
        return response['embedding']
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Генерація embedding через OpenAI"""
        model = self.rag_settings.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        
        response = self.openai_client.embeddings.create(
            model=model,
            input=text
        )
        
        return response.data[0].embedding
    
    def create_embedding_for_object(self, obj, language: str = 'uk') -> EmbeddingModel:
        """Створює embedding для Django об'єкта"""
        content_type = ContentType.objects.get_for_model(obj)
        
        # Витягуємо текст з об'єкта
        text_content = self._extract_text_from_object(obj, language)
        title = self._extract_title_from_object(obj, language)
        category = self._extract_category_from_object(obj)
        
        if not text_content:
            logger.warning(f"Немає тексту для індексації: {obj}")
            return None
        
        # Генеруємо embedding
        try:
            embedding_vector = self.generate_embedding(text_content)
        except Exception as e:
            logger.error(f"Не вдалося згенерувати embedding для {obj}: {e}")
            raise
        
        # Зберігаємо або оновлюємо
        embedding_obj, created = EmbeddingModel.objects.update_or_create(
            content_type=content_type,
            object_id=obj.pk,
            language=language,
            defaults={
                'embedding': embedding_vector,
                'content_text': text_content[:5000],  # Обмежуємо довжину
                'content_title': title,
                'content_category': category,
                'model_name': f"{self.embedding_model}-embedding",
                'is_active': True,
            }
        )
        
        action = "створено" if created else "оновлено"
        logger.info(f"Embedding {action} для {obj} ({language})")
        
        return embedding_obj
    
    def _extract_text_from_object(self, obj, language: str) -> str:
        """Витягує текст з Django об'єкта для індексації"""
        text_parts = []
        
        if isinstance(obj, ServiceCategory):
            title = getattr(obj, f'title_{language}', obj.title_en)
            description = getattr(obj, f'description_{language}', obj.description_en)
            short_desc = getattr(obj, f'short_description_{language}', obj.short_description_en)
            target_audience = getattr(obj, f'target_audience_{language}', obj.target_audience_en)
            value_prop = getattr(obj, f'value_proposition_{language}', obj.value_proposition_en)
            
            if title: text_parts.append(f"Сервіс: {title}")
            if description: text_parts.append(description)
            if short_desc: text_parts.append(short_desc)
            if target_audience: text_parts.append(f"Для кого: {target_audience}")
            if value_prop: text_parts.append(f"Переваги: {value_prop}")
            
        elif isinstance(obj, Project):
            title = getattr(obj, f'title_{language}', obj.title_en)
            short_desc = getattr(obj, f'short_description_{language}', obj.short_description_en)
            client_request = getattr(obj, f'client_request_{language}', obj.client_request_en)
            implementation = getattr(obj, f'implementation_{language}', obj.implementation_en)
            results = getattr(obj, f'results_{language}', obj.results_en)
            
            if title: text_parts.append(f"Проєкт: {title}")
            if short_desc: text_parts.append(short_desc)
            if client_request: text_parts.append(f"Завдання: {client_request}")
            if implementation: text_parts.append(f"Рішення: {implementation}")
            if results: text_parts.append(f"Результат: {results}")
            
        elif isinstance(obj, FAQ):
            question = getattr(obj, f'question_{language}', obj.question_en)
            answer = getattr(obj, f'answer_{language}', obj.answer_en)
            
            if question: text_parts.append(f"Питання: {question}")
            if answer: text_parts.append(f"Відповідь: {answer}")
        
        elif isinstance(obj, ServicePricing):
            # 💰 Витягуємо дані про ціни
            package_name = getattr(obj, f'package_name_{language}', obj.package_name_en)
            description = getattr(obj, f'description_{language}', obj.description_en)
            features = getattr(obj, f'features_{language}', obj.features_en)
            
            text_parts.append(f"Тарифний план: {package_name} для послуги {obj.service.title}")
            text_parts.append(f"Ціна: {obj.price} {obj.currency}")
            text_parts.append(f"Опис: {description}")
            if features:
                text_parts.append(f"Що входить: {', '.join(features)}")
        
        return '\n'.join(text_parts)
    
    def _extract_title_from_object(self, obj, language: str) -> str:
        """Витягує заголовок об'єкта"""
        if hasattr(obj, f'title_{language}'):
            return getattr(obj, f'title_{language}') or getattr(obj, 'title_en', str(obj))
        elif hasattr(obj, f'question_{language}'):  # FAQ
            return getattr(obj, f'question_{language}') or getattr(obj, 'question_en', str(obj))
        return str(obj)
    
    def _extract_category_from_object(self, obj) -> str:
        """Витягує категорію об'єкта"""
        if isinstance(obj, ServiceCategory):
            return 'service'
        elif isinstance(obj, Project):
            return 'project'
        elif isinstance(obj, FAQ):
            return 'faq'
        elif isinstance(obj, ServicePricing):
            return 'pricing'
        return 'unknown'


class VectorSearchService:
    """Сервіс для векторного пошуку"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.rag_settings = getattr(settings, 'RAG_SETTINGS', {})
        
    def search_similar_content(
        self, 
        query: str, 
        language: str = 'uk',
        limit: int = None,
        category: str = None,
        threshold: float = None
    ) -> List[Dict]:
        """Шукає схожий контент за допомогою векторного пошуку"""
        
        limit = limit or self.rag_settings.get('MAX_SEARCH_RESULTS', 10)
        threshold = threshold or self.rag_settings.get('SIMILARITY_THRESHOLD', 0.7)
        
        # Генеруємо embedding для запиту
        try:
            query_embedding = self.embedding_service.generate_embedding(query)
        except Exception as e:
            logger.error(f"Не вдалося згенерувати embedding для запиту '{query}': {e}")
            return []
        
        # Будуємо запит до БД
        queryset = EmbeddingModel.objects.filter(
            is_active=True,
            language=language
        )
        
        if category:
            queryset = queryset.filter(content_category=category)
        
        # Векторний пошук з cosine distance
        results = queryset.annotate(
            distance=CosineDistance('embedding', query_embedding)
        ).filter(
            distance__lt=(1 - threshold)  # Cosine distance: менше = схожіше
        ).order_by('distance')[:limit]
        
        # Форматуємо результати
        formatted_results = self._serialize_search_results(results)
        
        logger.info(f"Vector search для '{query}': знайдено {len(formatted_results)} результатів")
        return formatted_results

    def _serialize_search_results(self, results: List[EmbeddingModel]) -> List[Dict]:
        """Серіалізує результати векторного пошуку в JSON-сумісний формат."""
        serialized_results = []
        for result in results:
            obj = result.content_object
            if not obj:
                continue
            
            data = {
                'content_text': result.content_text,
                'content_title': result.content_title,
                'content_category': result.content_category,
                'similarity': round(1 - float(result.distance), 3),
                'metadata': result.metadata,
                'model_info': {
                    'app_label': result.content_type.app_label,
                    'model_name': result.content_type.model,
                    'pk': obj.pk,
                }
            }

            if hasattr(obj, 'get_absolute_url'):
                try:
                    data['url'] = obj.get_absolute_url()
                except Exception:
                    data['url'] = None
            
            if hasattr(obj, 'slug'):
                data['slug'] = obj.slug

            # Додаємо структуровані поля для прайсингу (ServicePricing)
            if result.content_type.app_label == 'pricing' and result.content_type.model == 'servicepricing':
                try:
                    data['price_from'] = float(getattr(obj, 'price_from', 0) or 0)
                    data['price_to'] = float(getattr(obj, 'price_to', 0) or 0) if getattr(obj, 'price_to', None) else None
                    data['currency'] = 'USD'
                    service_category = getattr(obj, 'service_category', None)
                    data['service_title'] = getattr(service_category, 'title_en', str(service_category)) if service_category else None
                    tier = getattr(obj, 'tier', None)
                    data['package_name'] = getattr(tier, 'display_name_en', str(tier)) if tier else None
                except Exception:
                    pass

            serialized_results.append(data)
        
        return serialized_results


class RAGConsultantService:
    """Головний RAG консультант"""
    
    def __init__(self):
        self.vector_search = VectorSearchService()
        self.embedding_service = EmbeddingService()
        self.rag_settings = getattr(settings, 'RAG_SETTINGS', {})
        
        # AI клієнт для генерації відповідей
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)

    def _contains_pricing_keywords(self, text: str) -> bool:
        t = (text or '').lower()
        return any(w in t for w in ['ціна', 'коштує', 'бюджет', 'price', 'вартість'])
    
    def process_user_query(
        self, 
        query: str, 
        session_id: str,
        language: str = 'uk'
    ) -> Dict:
        """Обробляє запит користувача через RAG"""
        
        # Отримуємо або створюємо сесію
        session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={'detected_intent': 'general'}
        )

        # Дістаємо метадані сесії
        meta = getattr(session, 'metadata', {}) or {}
        clar_asked = bool(meta.get('clarification_asked', False))
        
        # Векторний пошук релевантного контенту
        search_results = self.vector_search.search_similar_content(
            query=query,
            language=language,
            limit=5
        )
        
        # Аналізуємо намір користувача
        detected_intent = self._detect_user_intent(query, search_results)

        # Керування pricing-станом через metadata, без глобального "залипання"
        meta = getattr(session, 'metadata', {}) or {}
        awaiting = bool(meta.get('awaiting_pricing_details', False))
        completed = bool(meta.get('pricing_completed', False))

        if self._contains_pricing_keywords(query):
            detected_intent = 'pricing'
        elif awaiting and not completed:
            detected_intent = 'pricing'

        session.detected_intent = detected_intent
        session.total_messages += 1
        
        # Визначаємо, чи це фоллоуап (після першого питання асистента)
        recent_msgs = list(session.messages.order_by('-created_at')[:4])
        is_followup = any(m.role == 'assistant' for m in recent_msgs)

        # Жорстко обмежуємо уточнення одним заходом для pricing
        if detected_intent == 'pricing':
            allow_ask = (not clar_asked) and (not is_followup)
        else:
            allow_ask = False

        # Генеруємо відповідь
        response = self._generate_rag_response(
            query=query,
            search_results=search_results,
            language=language,
            intent=detected_intent,
            chat_history=session.messages.order_by('-created_at')[:4],
            is_followup=is_followup,
            allow_ask=allow_ask
        )

        # Гарантія показу кнопки прорахунку при текстових ознаках цін
        try:
            resp_text = (response.get('content') or '').lower()
            has_textual_price = any(
                key in resp_text for key in ['орієнтовн', 'вартіст', 'price', 'usd', '$']
            )
            if has_textual_price and not response.get('prices_ready', False):
                response['prices_ready'] = True
            if response.get('prices_ready'):
                actions = list(response.get('actions', []))
                has_quote_btn = any(
                    (a.get('type') == 'button' and a.get('action') == 'request_quote') for a in actions
                )
                if not has_quote_btn:
                    actions.append({
                        'type': 'button',
                        'text': '🧮 Отримати детальний прорахунок у PDF',
                        'action': 'request_quote',
                        'style': 'primary'
                    })
                response['actions'] = actions
        except Exception:
            pass

        # Якщо ми щойно задали уточнення для прайсингу — відмічаємо в метаданих
        if detected_intent == 'pricing' and allow_ask:
            meta['clarification_asked'] = True
        
        # Оновлюємо metadata стан для pricing (одноразове уточнення → очікуємо; коли ціни готові → завершуємо)
        resp = response
        if detected_intent == 'pricing' and allow_ask:
            meta['awaiting_pricing_details'] = True
        if detected_intent == 'pricing' and bool(resp.get('prices_ready')):
            meta['pricing_completed'] = True
            meta['awaiting_pricing_details'] = False

        session.metadata = meta
        session.save()
        
        # Зберігаємо повідомлення
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=query
        )
        
        ChatMessage.objects.create(
            session=session,
            role='assistant', 
            content=response['content'],
            rag_sources_used=[r['content_title'] for r in search_results],
            vector_search_results=search_results,
            ai_model_used='gemini-pro'
        )
        
        return {
            'response': response['content'],
            'intent': detected_intent,
            'sources': search_results,
            'suggestions': response.get('suggestions', []),
            'actions': response.get('actions', []),
            'prices_ready': response.get('prices_ready', False),
            'session_id': session_id
        }
    
    def _detect_user_intent(self, query: str, search_results: List[Dict]) -> str:
        """Визначає намір користувача"""
        query_lower = query.lower()
        
        # Ключові слова для кожного наміру
        if any(word in query_lower for word in ['ціна', 'скільки', 'коштує', 'бюджет', 'price']):
            return 'pricing'
        elif any(word in query_lower for word in ['консультація', 'зустріч', 'поговорити', 'consultation']):
            return 'consultation'
        elif any(word in query_lower for word in ['проєкт', 'портфоліо', 'кейс', 'приклад', 'project']):
            return 'portfolio'
        elif search_results and search_results[0]['content_category'] == 'service':
            return 'services'
        else:
            return 'general'
    
    def _generate_rag_response(
        self, 
        query: str, 
        search_results: List[Dict],
        language: str,
        intent: str,
        chat_history: List[ChatMessage],
        is_followup: bool,
        allow_ask: bool
    ) -> Dict:
        """Генерує відповідь на основі RAG контексту"""
        
        if not search_results:
            return self._generate_fallback_response(query, language, intent)
        
        # Будуємо контекст з найкращих результатів
        context_parts = []
        for result in search_results[:3]:  # Топ 3 результати
            context_parts.append(f"""
Джерело: {result['content_title']} (схожість: {result['similarity']})
Тип: {result['content_category']}
Контент: {result['content_text'][:800]}
""")
        
        context = "\n---\n".join(context_parts)
        
        # Формуємо історію чату для промпта
        history_text = ""
        if chat_history:
            history_lines = []
            for msg in reversed(chat_history):
                role = "Користувач" if msg.role == 'user' else "Асистент"
                history_lines.append(f"{role}: {msg.content}")
            history_text = "\n".join(history_lines)

        # Правило: жорсткий короткий флоу для pricing
        pricing_flow_mode = (intent == 'pricing')

        system_prompt = self._get_system_prompt(
            language,
            intent,
            is_first_message=(not history_text),
            is_followup=is_followup
        )

        if intent == 'pricing' and not is_followup:
            if allow_ask:
                system_prompt += "\nВажливо: це єдина серія уточнень у всій сесії."
            else:
                system_prompt += "\nНе став ніяких уточнень, одразу переходь до оцінок."
        
        user_prompt = f"""
Попередня розмова:
{history_text}

Контекст:
{context}

Запит користувача: {query}

Дай відповідь українською мовою на основі наданого контексту та попередньої розмови.
"""
        
        try:
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(
                f"{system_prompt}\n\n{user_prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )
            
            ai_response = response.text

            prices_ready = False
            prices = []
            # Якщо pricing і це фоллоуап — додаємо/підсилюємо ціни (без додаткових питань)
            if pricing_flow_mode and is_followup:
                pricing_lines = []
                for r in search_results:
                    if r.get('content_category') == 'pricing':
                        price_from = r.get('price_from')
                        price_to = r.get('price_to')
                        currency = r.get('currency', '')
                        pkg = r.get('package_name') or r.get('content_title')
                        service_title = r.get('service_title')
                        price_str = None
                        if price_from is not None and price_to is not None:
                            price_str = f"{price_from}-{price_to} {currency}".strip()
                        elif price_from is not None:
                            price_str = f"від {price_from} {currency}".strip()
                        elif price_to is not None:
                            price_str = f"до {price_to} {currency}".strip()
                        if (price_from is not None or price_to is not None) and pkg:
                            prices.append({
                                'title': f"{pkg}{f' ({service_title})' if service_title else ''}",
                                'description': '',
                                'price_from': price_from if price_from is not None else '',
                                'price_to': price_to if price_to is not None else '',
                                'currency': currency
                            })
                        if price_str and pkg:
                            line = f"- {pkg}: {price_str}"
                            if service_title:
                                line = f"{line} ({service_title})"
                            pricing_lines.append(line)
                pricing_lines = list(dict.fromkeys(pricing_lines))[:5]
                if pricing_lines:
                    prices_ready = True
                    if 'Ціни' not in ai_response:
                        ai_response = ai_response.strip() + "\n\nЦіни (орієнтовно):\n" + "\n".join(pricing_lines)

            # Резервне визначення наявності базових цін за текстом відповіді
            if not prices_ready:
                resp_lower = (ai_response or '').lower()
                if ('орієнтовн' in resp_lower) or ('$' in ai_response) or ('usd' in resp_lower) or ('вартіст' in resp_lower) or ('price' in resp_lower):
                    prices_ready = True

            # Одноразова згадка GDPR у першій відповіді в сесії
            is_first_assistant_reply = True
            if chat_history:
                for m in chat_history:
                    if m.role == 'assistant':
                        is_first_assistant_reply = False
                        break
            if is_first_assistant_reply:
                ai_response = ai_response.strip() + "\n\nЦе гарантує конфіденційність та відповідність стандартам GDPR."

            # Дії (CTA)
            actions = []
            consult_url = self.rag_settings.get('CONSULTATION_URL') or self.rag_settings.get('CONSULTATION_CALENDAR_URL')
            if consult_url:
                actions.append({
                    'type': 'link',
                    'text': 'Записатися на консультацію',
                    'url': consult_url,
                    'style': 'secondary',
                    'persistent': True
                })
            if prices_ready:
                actions.append({
                    'type': 'button',
                    'text': '🧮 Отримати детальний прорахунок у PDF',
                    'action': 'request_quote',
                    'style': 'primary'
                })
            
            suggestions = self._generate_suggestions(intent, search_results, language)
            
            return {
                'content': ai_response,
                'suggestions': suggestions,
                'context_used': len(search_results),
                'prices_ready': prices_ready,
                'actions': actions,
                'prices': prices
            }
            
        except Exception as e:
            logger.error(f"Помилка генерації RAG відповіді: {e}")
            return self._generate_fallback_response(query, language, intent)
    
    def _get_system_prompt(self, language: str, intent: str, is_first_message: bool, is_followup: bool) -> str:
        """Повертає системний промпт залежно від наміру"""
        
        consultant_name = self.rag_settings.get('CONSULTANT_NAME', 'Юлія')
        
        # 🚀 Динамічна інструкція для представлення
        intro_instruction = f"Представся як {consultant_name}, досвідчена IT консультантка компанії LazySoft, і привітайся." if is_first_message else ""
 
        # Правила для короткого флоу ціноутворення
        pricing_flow = ""
        if intent == 'pricing':
            if not is_followup:
                pricing_flow = (
                    "Після привітання задай ОДИН раз максимально повний перелік уточнень для оцінки, "
                    "у форматі нумерованого списку (1., 2., 3., 4.,5.), не більше 5 пунктів. "
                    "Не публікуй ціни у цьому повідомленні."
                )
            else:
                pricing_flow = (
                    "Це фоллоуап: не став додаткових питань. Дай ціни одразу після уточнень, використай наявні прайси; "
                    "якщо бракує даних, зроби короткі припущення (в дужках) і наведи діапазони."
                )
        
        base_prompt = f"""
{intro_instruction}
Ти допомагаєш клієнтам з технічними рішеннями та бізнес-автоматизацією.

Твоя поведінка:
- Відповідай професійно, але дружелюбно. Не представляйся, якщо це не перше повідомлення.
- Використовуй конкретні факти з контексту та попередньої розмови.
- Пропонуй практичні рішення.
- Завжди згадуй релевантні проєкти або сервіси.
- Не згадуй походження інформації та не пиши фрази на кшталт "з нашої бази знань".
- Якщо запит потребує уточнень, задай їх як нумерований список (1., 2., 3., 4., 5.), але тільки 1 раз, після давай ціни
- Не використовуй Markdown-розмітку (без **, без заголовків, без списків Markdown).
- Пропонуй записатися на безкоштовну консультацію або прорахунок
- Якщо в тебе немає відповіді на питання, скажи що ти нажаль не компенетна і запропонуй записатися на консультацію
{pricing_flow}
"""
        
        intent_prompts = {
            'pricing': f"""
{base_prompt}
Фокус на ціни: Коли говориш про ціни, завжди:
1. Уточнюй деталі проєкту перед називанням цін один раз
2. Пропонуй конкретні пакети (базовий/стандарт/преміум)
3. Згадуй приклади схожих проєктів
4. Пропонуй безкоштовну консультацію або прорахунок
""",
            'consultation': f"""
{base_prompt}
Фокус на консультації: 
1. Підкреслюй переваги особистого спілкування
2. Пропонуй конкретні часи для зустрічі
3. Готуй список питань для кращої підготовки
""",
            'services': f"""
{base_prompt}
Фокус на сервіси:
1. Детально розповідай про можливості
2. Наводь конкретні приклади використання  
3. Пропонуй супутні послуги
""",
            'portfolio': f"""
{base_prompt}
Фокус на проєкти:
1. Розповідай про конкретні кейси
2. Підкреслюй результати та ROI
3. Пропонуй схожі рішення
""",
        }
        
        return intent_prompts.get(intent, base_prompt)
    
    def _generate_suggestions(self, intent: str, search_results: List[Dict], language: str) -> List[str]:
        """Генерує персоналізовані пропозиції"""
        
        suggestions = []
        
        if intent == 'pricing':
            suggestions = [
                "📅 Записатися на консультацію"
            ]
        elif intent == 'consultation':
            suggestions = [
                "📅 Обрати зручний час для зустрічі",
                "📝 Підготувати список питань",
                "💼 Розповісти про ваш бізнес",
            ]
        
         
        
        return suggestions
    
    def _generate_fallback_response(self, query: str, language: str, intent: str) -> Dict:
        """Генерує відповідь коли не знайдено релевантного контенту"""
        
        fallback_responses = {
            'uk': {
                'pricing': "Щоб дати точну ціну, мені потрібно більше деталей про ваш проєкт. Розкажіть, будь ласка, що саме вас цікавить?",
                'consultation': "Я буду рада обговорити ваше питання на консультації. Коли вам буде зручно зустрітися?",
                'services': "Розкажіть більше про те, що вас цікавить, і я зможу запропонувати найкраще рішення.",
                'general': "Цікаве питання! Щоб дати максимально корисну відповідь, уточніть, будь ласка, деталі."
            }
        }
        
        response_text = fallback_responses.get(language, fallback_responses['uk']).get(intent, fallback_responses['uk']['general'])
        
        return {
            'content': response_text,
            'suggestions': [
                "💬 Уточнити питання",
                "📞 Зв'язатися з консультантом", 
                "📋 Переглянути наші сервіси"
            ],
            'context_used': 0
        }


class IndexingService:
    """Сервіс для індексації контенту"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.rag_settings = getattr(settings, 'RAG_SETTINGS', {})
    
    def index_all_content(self):
        """Індексує весь контент з визначених моделей"""
        
        indexable_models = self.rag_settings.get('INDEXABLE_MODELS', [])
        languages = self.rag_settings.get('SUPPORTED_LANGUAGES', ['uk'])
        
        total_indexed = 0
        
        for model_path in indexable_models:
            try:
                app_label, model_name = model_path.split('.')
                content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
                model_class = content_type.model_class()
                
                objects = model_class.objects.filter(is_active=True) if hasattr(model_class, 'is_active') else model_class.objects.all()
                
                for obj in objects:
                    for lang in languages:
                        try:
                            self.embedding_service.create_embedding_for_object(obj, lang)
                            total_indexed += 1
                        except Exception as e:
                            logger.error(f"Помилка індексації {obj} ({lang}): {e}")
                            continue
                            
                logger.info(f"Індексовано {objects.count()} об'єктів з {model_path}")
                
            except Exception as e:
                logger.error(f"Помилка індексації моделі {model_path}: {e}")
                continue
        
        logger.info(f"Загалом проіндексовано {total_indexed} записів")
        return total_indexed
    
    def reindex_object(self, obj):
        """Переіндексує конкретний об'єкт"""
        languages = self.rag_settings.get('SUPPORTED_LANGUAGES', ['uk'])
        
        for lang in languages:
            try:
                self.embedding_service.create_embedding_for_object(obj, lang)
            except Exception as e:
                logger.error(f"Помилка переіндексації {obj} ({lang}): {e}")
    
    def cleanup_orphaned_embeddings(self):
        """Видаляє embedding'и для видалених об'єктів"""
        deleted_count = 0
        
        for embedding in EmbeddingModel.objects.all():
            if not embedding.content_object:  # Об'єкт видалено
                embedding.delete()
                deleted_count += 1
        
        logger.info(f"Видалено {deleted_count} застарілих embedding'ів")
        return deleted_count