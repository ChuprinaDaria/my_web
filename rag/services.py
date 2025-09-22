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
        formatted_results = []
        for result in results:
            similarity = 1 - float(result.distance)  # Конвертуємо distance назад в similarity
            
            formatted_results.append({
                'object': result.content_object,
                'content_text': result.content_text,
                'content_title': result.content_title,
                'content_category': result.content_category,
                'similarity': round(similarity, 3),
                'metadata': result.metadata,
            })
        
        logger.info(f"Vector search для '{query}': знайдено {len(formatted_results)} результатів")
        return formatted_results


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
        
        # Векторний пошук релевантного контенту
        search_results = self.vector_search.search_similar_content(
            query=query,
            language=language,
            limit=5
        )
        
        # Аналізуємо намір користувача
        detected_intent = self._detect_user_intent(query, search_results)
        session.detected_intent = detected_intent
        session.total_messages += 1
        session.save()
        
        # Генеруємо відповідь на основі знайденого контенту
        response = self._generate_rag_response(
            query=query,
            search_results=search_results,
            language=language,
            intent=detected_intent
        )
        
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
        intent: str
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
        
        # Промпт для Gemini
        system_prompt = self._get_system_prompt(language, intent)
        user_prompt = f"""
Контекст з бази знань:
{context}

Запит користувача: {query}

Дай відповідь українською мовою на основі наданого контексту. Будь конкретною та корисною.
"""
        
        try:
            # Генеруємо відповідь через Gemini
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(
                f"{system_prompt}\n\n{user_prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )
            
            ai_response = response.text
            
            # Додаємо персоналізовані пропозиції
            suggestions = self._generate_suggestions(intent, search_results, language)
            
            return {
                'content': ai_response,
                'suggestions': suggestions,
                'context_used': len(search_results)
            }
            
        except Exception as e:
            logger.error(f"Помилка генерації RAG відповіді: {e}")
            return self._generate_fallback_response(query, language, intent)
    
    def _get_system_prompt(self, language: str, intent: str) -> str:
        """Повертає системний промпт залежно від наміру"""
        
        consultant_name = self.rag_settings.get('CONSULTANT_NAME', 'Юлія')
        
        base_prompt = f"""
Ти - {consultant_name}, досвідчена IT консультантка компанії LazySoft. 
Ти допомагаєш клієнтам з технічними рішеннями та бізнес-автоматизацією.

Твоя поведінка:
- Відповідай професійно, але дружелюбно
- Використовуй конкретні факти з контексту
- Пропонуй практичні рішення
- Завжди згадуй релевантні проєкти або сервіси
"""
        
        intent_prompts = {
            'pricing': f"""
{base_prompt}
Фокус на ціни: Коли говориш про ціни, завжди:
1. Уточнюй деталі проєкту перед називанням цін
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
                "🧮 Отримати детальний прорахунок",
                "📅 Записатися на безкоштовну консультацію",
                "📋 Переглянути схожі проєкти",
            ]
        elif intent == 'consultation':
            suggestions = [
                "📅 Обрати зручний час для зустрічі",
                "📝 Підготувати список питань",
                "💼 Розповісти про ваш бізнес",
            ]
        elif intent == 'services':
            # Пропонуємо супутні сервіси
            if search_results:
                categories = set(r.get('content_category') for r in search_results)
                if 'service' in categories:
                    suggestions.extend([
                        "🔍 Дізнатися більше про цей сервіс",
                        "💰 Переглянути пакети та ціни",
                        "📞 Обговорити ваші потреби",
                    ])
        elif intent == 'portfolio':
            suggestions = [
                "📊 Переглянути детальний кейс",
                "💡 Обговорити схоже рішення",
                "📈 Дізнатися про результати",
            ]
        else:
            suggestions = [
                "❓ Поставити уточнювальне питання",
                "📞 Зв'язатися з консультантом",
                "🏠 Повернутися на головну",
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