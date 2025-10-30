# rag/services.py
import os
import json
import logging
from typing import List, Dict, Tuple, Optional
from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from pgvector.django import CosineDistance
from openai import OpenAI
from django.utils import timezone
import numpy as np

from .models import EmbeddingModel, ChatSession, ChatMessage, RAGAnalytics, KnowledgeSource
from services.models import ServiceCategory, FAQ
from projects.models import Project
from pricing.models import ServicePricing
from .utils import get_active_embedding_conf # Імпортуємо утиліту

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Сервіс для генерації та управління embedding'ами"""
    
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)

        # Налаштування з settings
        self.rag_settings = getattr(settings, 'RAG_SETTINGS', {})

        # Отримуємо конфігурацію активної моделі embeddings
        self.active_embedding_conf = get_active_embedding_conf()
        self.embedding_model_name = self.active_embedding_conf["name"]
        self.embedding_dimensions = self.active_embedding_conf["dim"]

        # Ініціалізація AI клієнтів - тільки OpenAI
        self.openai_client = None

        self._init_embedding_clients()
    
    def _init_embedding_clients(self):
        # Ініціалізація OpenAI клієнта - тільки OpenAI
        if self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI embedding клієнт ініціалізовано")
            except Exception as e:
                self.openai_client = None
                logger.error(f"❌ Помилка ініціалізації OpenAI embedding клієнта: {e}")
        else:
            logger.warning("OpenAI API ключ для embedding не встановлено.")

    def generate_embedding(self, text: str, model_provider: str = None) -> Tuple[List[float], str]:
        """Генерує embedding для тексту з фолбеком"""
        if not text.strip():
            raise ValueError("Текст не може бути пустим")
            
        provider_to_use = (
            model_provider
            or self.active_embedding_conf.get("provider")
            or self.rag_settings.get("PROVIDER", "openai")
        )
        expected_dim = int(self.embedding_dimensions or self.active_embedding_conf.get("dim") or 0)
        if expected_dim <= 0:
            raise ValueError("Невірна розмірність embedding (<= 0)")

        def _ensure_vector_dim(vec, provider_name, target_dim):
            import numpy as np

            if isinstance(vec, dict) and "embedding" in vec:
                vec = vec["embedding"]

            if isinstance(vec, list) and vec and isinstance(vec[0], (list, tuple)):
                vec = vec[0]

            try:
                arr = np.asarray(vec, dtype=float)
            except Exception as err:
                raise ValueError(f"Embedding від {provider_name} має невірний формат: {err}")

            arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
            if arr.ndim != 1:
                arr = arr.flatten()

            if arr.size == target_dim:
                return arr.tolist()

            logger.warning(
                "[EMBEDDING] Модель %s повернула розмірність %s, очікували %s — робимо підгін.",
                provider_name,
                arr.size,
                target_dim,
            )

            if arr.size > target_dim:
                arr = arr[:target_dim]
            else:
                arr = np.pad(arr, (0, target_dim - arr.size), mode="constant")

            return arr.tolist()

        # Використовуємо тільки OpenAI
        try:
            if self.openai_client:
                embedding = self._call_openai_embedding(text)
                return _ensure_vector_dim(embedding, "openai", expected_dim), "openai"
            else:
                raise Exception("OpenAI клієнт не ініціалізовано")
        except Exception as e:
            logger.error("[EMBEDDING] Помилка OpenAI embedding: %s", e)
            raise Exception("OpenAI embedding модель недоступна")
    
    def _call_openai_embedding(self, text: str) -> List[float]:
        """Генерація embedding через OpenAI"""
        # Завжди використовуємо налаштування активної моделі для OpenAI, якщо вона активна
        if self.active_embedding_conf["provider"] == "openai":
            model_name = self.embedding_model_name
            expected_dim = self.embedding_dimensions
        else:
            # Якщо OpenAI не активний провайдер, беремо дефолтні налаштування для OpenAI
            model_name = self.rag_settings.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
            expected_dim = self.rag_settings.get('OPENAI_EMBEDDING_DIMENSIONS', 1536)
        
        response = self.openai_client.embeddings.create(
            model=model_name,
            input=text,
            dimensions=expected_dim # Задаємо розмірність явно
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
            embedding_vector, model_name_used = self.generate_embedding(text_content)
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
                'model_name': f"{model_name_used}-embedding",
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
        elif obj.__class__.__name__ == 'Contact':
            # Контактна сторінка (contacts.Contact)
            title = getattr(obj, f'title_{language}', getattr(obj, 'title_en', 'Contact'))
            description = getattr(obj, f'description_{language}', getattr(obj, 'description_en', '')) or ''
            address = getattr(obj, f'address_line_1_{language}', getattr(obj, 'address_line_1_en', ''))
            city = getattr(obj, 'city', '')
            country = getattr(obj, f'country_{language}', getattr(obj, 'country_en', ''))
            email = getattr(obj, 'email', '')
            phone = getattr(obj, 'phone', '')
            if title: text_parts.append(f"Сторінка: {title}")
            if description: text_parts.append(description)
            text_parts.append(f"Email: {email} | Телефон: {phone}")
            if address or city or country:
                text_parts.append(f"Адреса: {address}, {city}, {country}".strip(', '))
        elif obj.__class__.__name__ == 'About':
            # Сторінка About (about.About)
            title = getattr(obj, f'title_{language}', getattr(obj, 'title_en', 'About'))
            mission = getattr(obj, f'mission_{language}', getattr(obj, 'mission_en', '')) or ''
            story = getattr(obj, f'story_{language}', getattr(obj, 'story_en', '')) or ''
            services = getattr(obj, f'services_{language}', getattr(obj, 'services_en', '')) or ''
            if title: text_parts.append(f"Сторінка: {title}")
            if mission: text_parts.append(f"Місія: {mission}")
            if story: text_parts.append(f"Історія: {story}")
            if services: text_parts.append(f"Що робимо: {services}")
        elif isinstance(obj, KnowledgeSource):
            # Ручне джерело знань (rag.KnowledgeSource)
            title = getattr(obj, 'title', '')
            # Контент потрібною мовою з фолбеком
            lang_content = (
                getattr(obj, f'content_{language}', '')
                or getattr(obj, 'content_uk', '')
                or getattr(obj, 'content_en', '')
                or getattr(obj, 'content_pl', '')
                or ''
            )
            if title:
                text_parts.append(f"Джерело: {title}")
            if lang_content:
                text_parts.append(lang_content)
        
        elif isinstance(obj, ServicePricing):
            # 💰 Витягуємо дані про ціни з реальної моделі pricing.ServicePricing
            service_category = getattr(obj, 'service_category', None)
            category_title = ''
            if service_category:
                category_title = getattr(service_category, f'title_{language}', getattr(service_category, 'title_en', str(service_category)))

            tier = getattr(obj, 'tier', None)
            tier_name = ''
            if tier:
                tier_name = getattr(tier, f'display_name_{language}', getattr(tier, 'display_name_en', str(tier)))

            price_from = getattr(obj, 'price_from', None)
            price_to = getattr(obj, 'price_to', None)
            timeline_from = getattr(obj, 'timeline_weeks_from', None)
            timeline_to = getattr(obj, 'timeline_weeks_to', None)

            features_text = getattr(obj, f'features_included_{language}', getattr(obj, 'features_included_en', '')) or ''

            if category_title or tier_name:
                text_parts.append(f"Сервіс: {category_title} — пакет: {tier_name}".strip())

            # Опис ціни
            if price_from is not None and price_to:
                text_parts.append(f"Діапазон ціни: ${int(price_from):,} - ${int(price_to):,}")
            elif price_from is not None:
                text_parts.append(f"Ціна від: ${int(price_from):,}")
            elif price_to is not None:
                text_parts.append(f"Ціна до: ${int(price_to):,}")

            # Термін виконання
            if timeline_from and timeline_to:
                text_parts.append(f"Термін: {timeline_from}-{timeline_to} тижнів")
            elif timeline_from:
                text_parts.append(f"Термін: {timeline_from} тижнів")

            # Що входить
            if features_text:
                # беремо перші 10 рядків, щоб не перевищувати ліміт
                lines = [line.strip() for line in features_text.split('\n') if line.strip()]
                if lines:
                    text_parts.append("Що входить: " + "; ".join(lines[:10]))
        
        return '\n'.join(text_parts)
    
    def _extract_title_from_object(self, obj, language: str) -> str:
        """Витягує заголовок об'єкта"""
        if obj.__class__.__name__ == 'Contact':
            return getattr(obj, f'title_{language}', getattr(obj, 'title_en', 'Contact'))
        if obj.__class__.__name__ == 'About':
            return getattr(obj, f'title_{language}', getattr(obj, 'title_en', 'About'))
        if isinstance(obj, KnowledgeSource):
            return getattr(obj, 'title', str(obj))
        if isinstance(obj, ServicePricing):
            # Заголовок для ціни: Назва пакета + сервіс
            service_category = getattr(obj, 'service_category', None)
            category_title = ''
            if service_category:
                category_title = getattr(service_category, f'title_{language}', getattr(service_category, 'title_en', str(service_category)))
            tier = getattr(obj, 'tier', None)
            tier_name = ''
            if tier:
                tier_name = getattr(tier, f'display_name_{language}', getattr(tier, 'display_name_en', str(tier)))
            title = tier_name or 'Pricing'
            if category_title:
                title = f"{title} ({category_title})"
            return title
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
        elif obj.__class__.__name__ == 'Contact':
            return 'contact'
        elif obj.__class__.__name__ == 'About':
            return 'about'
        elif isinstance(obj, KnowledgeSource):
            return getattr(obj, 'source_type', 'manual') or 'manual'
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
        threshold: float = None,
        diversify: bool = True
    ) -> List[Dict]:
        """Шукає схожий контент за допомогою векторного пошуку"""
        
        limit = limit or self.rag_settings.get('MAX_SEARCH_RESULTS', 10)
        threshold = threshold or self.rag_settings.get('SIMILARITY_THRESHOLD', 0.7)
        
        # Генеруємо embedding для запиту
        try:
            vec, _provider = self.embedding_service.generate_embedding(query)
            arr = np.asarray(vec, dtype=float).flatten()
            query_embedding = arr.tolist()
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
        # Для диверсифікації беремо більше результатів
        fetch_limit = limit * 3 if diversify else limit
        results = queryset.annotate(
            distance=CosineDistance('embedding', query_embedding)
        ).filter(
            distance__lt=(1 - threshold)  # Cosine distance: менше = схожіше
        ).order_by('distance')[:fetch_limit]
        
        # Форматуємо результати
        formatted_results = self._serialize_search_results(results)
        
        # Диверсифікуємо результати якщо потрібно
        if diversify and len(formatted_results) > limit:
            formatted_results = self._diversify_results(formatted_results, limit)
        
        logger.info(f"Vector search для '{query}': знайдено {len(formatted_results)} результатів")
        return formatted_results
        
    def _diversify_results(self, results: List[Dict], limit: int) -> List[Dict]:
        """Диверсифікує результати пошуку для уникнення домінування одного сервісу"""
        diversified = []
        seen_services = {}
        max_per_service = 2  # Максимум 2 результати з одного сервісу
        
        # Спершу додаємо по 1 результату з кожного унікального сервісу
        for result in results:
            # Визначаємо сервіс з тексту або metadata
            service_key = None
            if 'service_title' in result and result['service_title']:
                service_key = result['service_title']
            elif 'content_title' in result:
                # Витягуємо назву сервісу з заголовку
                title = result['content_title']
                if 'Чат-боти' in title or 'Chatbot' in title or 'Chat bot' in title:
                    service_key = 'chatbot'
                elif 'CRM' in title:
                    service_key = 'crm'
                elif 'ETL' in title or 'Автоматизація даних' in title:
                    service_key = 'etl'
                elif 'Лендінг' in title or 'Landing' in title:
                    service_key = 'landing'
                elif 'SEO' in title:
                    service_key = 'seo'
                else:
                    service_key = result.get('content_category', 'other')
            else:
                service_key = result.get('content_category', 'other')
            
            # Рахуємо кількість результатів для цього сервісу
            if service_key not in seen_services:
                seen_services[service_key] = 0
            
            # Додаємо якщо не перевищено ліміт для сервісу
            if seen_services[service_key] < max_per_service:
                diversified.append(result)
                seen_services[service_key] += 1
                
                if len(diversified) >= limit:
                    break
        
        # Якщо недостатньо результатів, додаємо решту найкращих
        if len(diversified) < limit:
            for result in results:
                if result not in diversified:
                    diversified.append(result)
                    if len(diversified) >= limit:
                        break
        
        return diversified[:limit]

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

        # AI клієнт для генерації відповідей - тільки OpenAI
        self.openai_client = None

        self.preferred_model = 'openai'
        self.backup_model = None

        # Додаємо API ключі для генеративних моделей
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)

        self._init_generative_clients()

    def _init_generative_clients(self):
        # Тільки OpenAI
        org = getattr(settings, "OPENAI_ORG_ID", "") or None
        proj = getattr(settings, "OPENAI_PROJECT_ID", "") or None
        api_key = getattr(settings, "OPENAI_API_KEY", "")

        if api_key:
            try:
                self.openai_client = OpenAI(
                    api_key=api_key,
                    organization=org,
                    project=proj,
                )
                logger.info("RAG OpenAI клієнт ініціалізовано (org=%s, project=%s)", org or "-", proj or "-")
            except Exception as e:
                self.openai_client = None
                logger.error("RAG OpenAI клієнт не ініціалізувався: %s", e)
        else:
            logger.warning("RAG OpenAI API ключ не встановлено.")

    def _call_generative_ai_model(self, prompt: str, max_tokens: int) -> Tuple[str, str]:
        """Універсальний виклик AI для генерації - тільки OpenAI."""
        temperature = getattr(settings, 'AI_TEMPERATURE', 0.7)
        max_output_tokens = getattr(settings, 'AI_MAX_TOKENS', 1000)

        # Використовуємо OpenAI
        try:
            if self.openai_client:
                logger.info(f"[RAG AI] Використовуємо OpenAI ({getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL', 'gpt-4o')})...")
                response = self._call_openai_generative(prompt, max_output_tokens, temperature)
                return response, 'openai'
            else:
                raise Exception("OpenAI клієнт не ініціалізовано")
        except Exception as e:
            logger.error(f"[RAG AI] Помилка OpenAI: {e}")
            # Спробуємо fallback модель
            try:
                logger.info(f"[RAG AI] Спробуємо OpenAI Fallback ({getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL_FALLBACK', 'gpt-4o-mini')})...")
                response = self._call_openai_generative(prompt, max_output_tokens, temperature, is_fallback=True)
                return response, 'openai'
            except Exception as fallback_e:
                logger.error(f"❌ RAG OpenAI Fallback теж недоступна: {fallback_e}")
                raise Exception("❌ OpenAI модель недоступна для RAG.")

    def _call_openai_generative(self, prompt: str, max_tokens: int, temperature: float, is_fallback: bool = False) -> str:
        """Виклик OpenAI GPT для генерації."""
        model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL', 'gpt-4o')
        if is_fallback:
            model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL_FALLBACK', 'gpt-4o-mini')

        logger.info(f"[RAG OpenAI] Відправляємо запит до моделі {model_name} довжиною {len(prompt)} символів...")
        try:
            resp = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            logger.info(f"[RAG OpenAI] Успішна відповідь від {model_name}: {len(resp.choices[0].message.content)} символів")
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"[RAG OpenAI] Помилка від {model_name}: {e}")
            raise

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
        # Для питань про сервіси збираємо більше результатів
        search_limit = 15 if 'сервіс' in query.lower() or 'послуг' in query.lower() else 5
        search_results = self.vector_search.search_similar_content(
            query=query,
            language=language,
            limit=search_limit
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
        response_data, model_used = self._generate_rag_response(
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
            resp_text = (response_data.get('content') or '').lower()
            has_textual_price = any(
                key in resp_text for key in ['орієнтовн', 'вартіст', 'price', 'usd', '$']
            )
            if has_textual_price and not response_data.get('prices_ready', False):
                response_data['prices_ready'] = True
            if response_data.get('prices_ready'):
                actions = list(response_data.get('actions', []))
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
                response_data['actions'] = actions
        except Exception:
            pass

        # Якщо ми щойно задали уточнення для прайсингу — відмічаємо в метаданих
        if detected_intent == 'pricing' and allow_ask:
            meta['clarification_asked'] = True
        
        # Оновлюємо metadata стан для pricing (одноразове уточнення → очікуємо; коли ціни готові → завершуємо)
        resp = response_data
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
            content=response_data['content'],
            rag_sources_used=[r['content_title'] for r in search_results],
            vector_search_results=search_results,
            ai_model_used=model_used
        )
        
        return {
            'response': response_data['content'],
            'intent': detected_intent,
            'sources': search_results,
            'suggestions': response_data.get('suggestions', []),
            'actions': response_data.get('actions', []),
            'prices_ready': response_data.get('prices_ready', False),
            'session_id': session_id
        }
    
    def _detect_user_intent(self, query: str, search_results: List[Dict]) -> str:
        """Визначає намір користувача"""
        query_lower = query.lower()
        
        # Привітання мають найвищий пріоритет
        if any(word in query_lower for word in ['привіт', 'вітаю', 'доброго дня', 'добрий день', 
                                                  'доброго ранку', 'hello', 'hi', 
                                                  'hey', 'здрастуйте']) and len(query_lower) < 30:
            return 'greeting'
        # Ключові слова для кожного наміру
        elif any(word in query_lower for word in ['ціна', 'скільки', 'коштує', 'бюджет', 'price', 'вартість']):
            return 'pricing'
        elif any(word in query_lower for word in ['консультація', 'зустріч', 'поговорити', 'consultation']):
            return 'consultation'
        elif any(word in query_lower for word in ['проєкт', 'портфоліо', 'кейс', 'приклад', 'project']):
            return 'portfolio'
        elif any(word in query_lower for word in ['сервіс', 'послуг', 'пропонуєте', 'робите', 'займаєтесь']):
            return 'services'
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
    ) -> Tuple[Dict, str]:
        """Генерує відповідь на основі RAG контексту"""
        
        if not search_results:
            # Fallback відповідь, якщо немає релевантного контенту
            return self._generate_fallback_response(query, language, intent), "fallback"
        
        # Будуємо контекст з найкращих результатів
        context_parts = []
        
        # Для питань про сервіси збираємо всі унікальні сервіси
        if intent == 'services':
            seen_services = set()
            service_contexts = []
            service_from_pricing = {}
            other_contexts = []
            
            for result in search_results:
                if result['content_category'] == 'service':
                    service_title = result['content_title']
                    if service_title not in seen_services:
                        seen_services.add(service_title)
                        service_contexts.append(f"""
Сервіс: {result['content_title']}
Контент: {result['content_text'][:500]}
""")
                elif result['content_category'] == 'pricing':
                    # Витягуємо інформацію про сервіси з pricing
                    service_title = result.get('service_title', '')
                    if service_title and service_title not in service_from_pricing:
                        service_from_pricing[service_title] = []
                    if service_title:
                        service_from_pricing[service_title].append({
                            'package': result.get('package_name', ''),
                            'price_from': result.get('price_from', ''),
                            'price_to': result.get('price_to', ''),
                            'text': result['content_text'][:200]
                        })
                elif len(other_contexts) < 2:  # Додаємо максимум 2 інших результати
                    other_contexts.append(f"""
Джерело: {result['content_title']} (тип: {result['content_category']})
Контент: {result['content_text'][:300]}
""")
            
            # Додаємо сервіси знайдені в pricing якщо їх немає в service
            for service_name, pricing_info in service_from_pricing.items():
                if service_name not in seen_services:
                    seen_services.add(service_name)
                    # Беремо перший pricing запис для опису
                    info = pricing_info[0]
                    service_contexts.append(f"""
Сервіс: {service_name}
Опис: {info['text']}
Пакети: {', '.join(p['package'] for p in pricing_info[:3] if p['package'])}
""")
            
            # Об'єднуємо контексти, пріоритет сервісам
            context_parts = service_contexts[:7] + other_contexts
        else:
            # Для інших намірів використовуємо топ результати
            for result in search_results[:3]:
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
"""
        
        ai_response_content, model_used = self._call_generative_ai_model(
            prompt=f"{system_prompt}\n\n{user_prompt}",
            max_tokens=getattr(settings, 'AI_MAX_TOKENS', 1000)
        )

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
            if 'Ціни' not in ai_response_content:
                ai_response_content = ai_response_content.strip() + "\n\nЦіни (орієнтовно):\n" + "\n".join(pricing_lines)

        # Резервне визначення наявності базових цін за текстом відповіді
        if not prices_ready:
            resp_lower = (ai_response_content or '').lower()
            if ('орієнтовн' in resp_lower) or ('$' in ai_response_content) or ('usd' in resp_lower) or ('вартіст' in resp_lower) or ('price' in resp_lower):
                prices_ready = True

        # Одноразова згадка GDPR у першій відповіді в сесії
        is_first_assistant_reply = True
        if chat_history:
            for m in chat_history:
                if m.role == 'assistant':
                    is_first_assistant_reply = False
                    break
        if is_first_assistant_reply:
            ai_response_content = ai_response_content.strip() + "\n\nЦе гарантує конфіденційність та відповідність стандартам GDPR."

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
            'content': ai_response_content,
            'suggestions': suggestions,
            'context_used': len(search_results),
            'prices_ready': prices_ready,
            'actions': actions,
            'prices': prices
        }, model_used
    
    def _get_system_prompt(self, language: str, intent: str, is_first_message: bool, is_followup: bool) -> str:
        """Повертає системний промпт залежно від наміру"""
        
        consultant_name = self.rag_settings.get('CONSULTANT_NAME', 'Юлія')
        
        # Визначаємо мову для інструкцій
        lang_instructions = {
            'uk': {
                'intro': f"Представся як {consultant_name}, досвідчена IT консультантка компанії LazySoft, і привітайся.",
                'language': "Відповідай українською мовою.",
                'behavior': """Твоя поведінка:
- Відповідай професійно, але дружелюбно. Не представляйся, якщо це не перше повідомлення.
- Використовуй конкретні факти з контексту та попередньої розмови.
- Пропонуй практичні рішення.
- Згадуй релевантні проєкти або сервіси ТІЛЬКИ якщо користувач питає про них або це доречно в контексті.
- Не згадуй походження інформації та не пиши фрази на кшталт "з нашої бази знань".
- Якщо запит потребує уточнень, задай їх як нумерований список (1., 2., 3., 4., 5.), але тільки 1 раз, після давай ціни
- Не використовуй Markdown-розмітку (без **, без заголовків, без списків Markdown).
- Пропонуй записатися на безкоштовну консультацію або прорахунок коли це доречно
- Якщо в тебе немає відповіді на питання, скажи що ти нажаль не компенетна і запропонуй записатися на консультацію""",
                'pricing_ask': "Після привітання задай ОДИН раз максимально повний перелік уточнень для оцінки, у форматі нумерованого списку (1., 2., 3., 4., 5.), не більше 5 пунктів. Не публікуй ціни у цьому повідомленні.",
                'pricing_followup': "Це фоллоуап: не став додаткових питань. Дай ціни одразу після уточнень, використай наявні прайси; якщо бракує даних, зроби короткі припущення (в дужках) і наведи діапазони."
            },
            'pl': {
                'intro': f"Przedstaw się jako {consultant_name}, doświadczona konsultantka IT w firmie LazySoft, i przywitaj się.",
                'language': "Odpowiadaj po polsku.",
                'behavior': """Twoje zachowanie:
- Odpowiadaj profesjonalnie, але przyjaźnie. Nie przedstawiaj się, jeśli to nie pierwsza wiadomość.
- Używaj konkretnych faktów z kontekstu i poprzedniej rozmowy.
- Proponuj praktyczne rozwiązania.
- Wspominaj o odpowiednich projektach lub usługach TYLKO jeśli użytkownik o nie pyta lub jest to stosowne w kontekście.
- Nie wspominaj o pochodzeniu informacji i nie pisz fraz typu "z naszej bazy wiedzy".
- Jeśli zapytanie wymaga wyjaśnień, zadaj je jako listę numerowaną (1., 2., 3., 4., 5.), ale tylko RAZ, potem podaj ceny
- Nie używaj formatowania Markdown (bez **, bez nagłówków, bez list Markdown).
- Proponuj umówienie się na bezpłatną konsultację lub wycenę, gdy to stosowne
- Jeśli nie masz odpowiedzi na pytanie, powiedz że niestety nie jesteś kompetentna i zaproponuj konsultację""",
                'pricing_ask': "Po przywitaniu zadaj JEDEN raz maksymalnie pełną listę pytań do wyceny, w formacie listy numerowanej (1., 2., 3., 4., 5.), nie więcej niż 5 punktów. Nie publikuj cen w tej wiadomości.",
                'pricing_followup': "To follow-up: nie zadawaj dodatkowych pytań. Podaj ceny od razu po wyjaśnieniach, użyj dostępnych cenników; jeśli brakuje danych, zrób krótkie założenia (w nawiasach) i podaj zakresy."
            },
            'en': {
                'intro': f"Introduce yourself as {consultant_name}, an experienced IT consultant at LazySoft, and say hello.",
                'language': "Respond in English.",
                'behavior': """Your behavior:
- Respond professionally but friendly. Don't introduce yourself if it's not the first message.
- Use specific facts from context and previous conversation.
- Offer practical solutions.
- Mention relevant projects or services ONLY if the user asks about them or it's appropriate in context.
- Don't mention the source of information and don't write phrases like "from our knowledge base".
- If the request needs clarification, ask them as a numbered list (1., 2., 3., 4., 5.), but only ONCE, then give prices
- Don't use Markdown formatting (no **, no headers, no Markdown lists).
- Offer to schedule a free consultation or quote when appropriate
- If you don't have an answer to a question, say you're unfortunately not competent and offer a consultation""",
                'pricing_ask': "After greeting, ask ONCE a maximally complete list of clarifications for pricing, in numbered list format (1., 2., 3., 4., 5.), no more than 5 points. Don't publish prices in this message.",
                'pricing_followup': "This is a follow-up: don't ask additional questions. Give prices immediately after clarifications, use available price lists; if data is missing, make brief assumptions (in parentheses) and provide ranges."
            }
        }
        
        lang_data = lang_instructions.get(language, lang_instructions['uk'])
        intro_instruction = lang_data['intro'] if is_first_message else ""
 
        # Правила для короткого флоу ціноутворення
        pricing_flow = ""
        if intent == 'pricing':
            if not is_followup:
                pricing_flow = lang_data['pricing_ask']
            else:
                pricing_flow = lang_data['pricing_followup']
        
        base_prompt = f"""
{intro_instruction}
{lang_data['language']}
{lang_data['behavior']}
{pricing_flow}
"""
        
        intent_prompts = {
            'greeting': f"""
{base_prompt}
{self._get_greeting_instructions(language)}
""",
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
Фокус на сервіси - ВАЖЛИВО:
1. Обов'язково перерахуй ВСІ основні послуги компанії, які згадані в контексті
2. Дай короткий опис кожної послуги (2-3 речення)
3. НЕ фокусуйся тільки на одній послузі, навіть якщо про неї більше інформації
4. Якщо в контексті згадуються: чат-боти, CRM, лендінги, автоматизація даних (ETL) - згадай їх всі
5. Наприкінці запропонуй обговорити деталі на консультації
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
        
        suggestions_by_lang = {
            'uk': {
                'greeting': [
                    "💼 Які послуги ми надаємо?",
                    "💰 Дізнатися про ціни", 
                "📅 Записатися на консультацію"
                ],
                'pricing': [
                    "📅 Записатися на консультацію"
                ],
                'consultation': [
                "📅 Обрати зручний час для зустрічі",
                "📝 Підготувати список питань",
                "💼 Розповісти про ваш бізнес",
                ],
                'default': [
                    "💬 Уточнити питання",
                    "📞 Зв'язатися з консультантом",
                    "📋 Переглянути наші сервіси",
                ]
            },
            'pl': {
                'greeting': [
                    "💼 Jakie usługi oferujemy?",
                    "💰 Dowiedz się o cenach",
                    "📅 Umów konsultację"
                ],
                'pricing': [
                    "📅 Umów konsultację"
                ],
                'consultation': [
                    "📅 Wybierz dogodny termin spotkania",
                    "📝 Przygotuj listę pytań",
                    "💼 Opowiedz o swoim biznesie",
                ],
                'default': [
                    "💬 Doprecyzuj pytanie",
                    "📞 Skontaktuj się z konsultantem",
                    "📋 Zobacz nasze usługi",
                ]
            },
            'en': {
                'greeting': [
                    "💼 What services do we offer?",
                    "💰 Learn about pricing",
                    "📅 Schedule a consultation"
                ],
                'pricing': [
                    "📅 Schedule a consultation"
                ],
                'consultation': [
                    "📅 Choose a convenient meeting time",
                    "📝 Prepare your questions",
                    "💼 Tell us about your business",
                ],
                'default': [
                    "💬 Clarify the question",
                    "📞 Contact a consultant",
                    "📋 View our services",
                ]
            }
        }
        
        lang_suggestions = suggestions_by_lang.get(language, suggestions_by_lang['uk'])
        suggestions = lang_suggestions.get(intent, lang_suggestions.get('default', []))
        
        return suggestions
    
    def _get_greeting_instructions(self, language: str) -> str:
        """Повертає інструкції для привітання залежно від мови"""
        greeting_instructions = {
            'uk': """При привітанні:
1. Привітайся дружелюбно та професійно
2. Коротко розкажи про LazySoft як IT компанію (1-2 речення)
3. Запитай, чим можеш допомогти або що цікавить користувача
4. НЕ згадуй конкретні сервіси або ціни, якщо користувач не питав
5. НЕ нав'язуй інформацію про послуги""",
            'pl': """Przy powitaniu:
1. Przywitaj się przyjaźnie i profesjonalnie
2. Krótko opowiedz o LazySoft jako firmie IT (1-2 zdania)
3. Zapytaj, w czym możesz pomóc lub co interesuje użytkownika
4. NIE wspominaj o konkretnych usługach lub cenach, jeśli użytkownik nie pytał
5. NIE narzucaj informacji o usługach""",
            'en': """When greeting:
1. Greet friendly and professionally
2. Briefly tell about LazySoft as an IT company (1-2 sentences)
3. Ask how you can help or what interests the user
4. DON'T mention specific services or prices if the user didn't ask
5. DON'T impose information about services"""
        }
        return greeting_instructions.get(language, greeting_instructions['uk'])
    
    def _generate_fallback_response(self, query: str, language: str, intent: str) -> Dict:
        """Генерує відповідь коли не знайдено релевантного контенту"""
        
        fallback_responses = {
            'uk': {
                'greeting': "Привіт! Я Юлія, IT консультантка LazySoft. Ми допомагаємо бізнесу з автоматизацією та розробкою технічних рішень. Чим можу допомогти?",
                'pricing': "Щоб зорієнтувати по бюджету, розкажіть, будь ласка, про тип продукту, ключові функції та бажані терміни — і я підкажу діапазон.",
                'consultation': "Я буду рада обговорити ваше питання на консультації. Коли вам буде зручно зустрітися?",
                'services': "Ми в LazySoft розробляємо чат-боти, CRM-рішення, landing page, автоматизації даних та аналітичні панелі. Напишіть, який напрям вам цікавий, і я підкажу, з чого почати.",
                'general': "З радістю допоможу! Ми в LazySoft створюємо IT-рішення під ключ: від чат-ботів і CRM до landing page та автоматизацій даних. Розкажіть, будь ласка, що саме плануєте — і я підкажу найкращий формат співпраці."
            },
            'pl': {
                'greeting': "Cześć! Jestem Julia, konsultantka IT w LazySoft. Pomagamy firmom automatyzować procesy i budować rozwiązania cyfrowe. Jak mogę pomóc?",
                'pricing': "Aby podać budżet, daj proszę znać, jaki produkt planujesz, jakie funkcje są kluczowe i jaki masz termin — od razu zaproponuję widełki cenowe.",
                'consultation': "Chętnie omówię Twój temat na konsultacji. Kiedy pasuje Ci spotkanie online?",
                'services': "W LazySoft tworzymy chatboty, systemy CRM, landing page, automatyzacje danych i pulpity analityczne. Napisz, które rozwiązanie Cię interesuje, a zaproponuję następne kroki.",
                'general': "Z przyjemnością pomogę! W LazySoft budujemy rozwiązania IT dopasowane do biznesu: chatboty, CRM, strony landing oraz automatyzacje danych. Powiedz, czego dokładnie potrzebujesz, a doradzę najlepsze wyjście."
            },
            'en': {
                'greeting': "Hello! I'm Julia, an IT consultant at LazySoft. We help businesses automate processes and craft digital solutions. How can I assist you today?",
                'pricing': "To suggest a budget range, let me know what kind of product you have in mind, the key features and the timeline — I'll outline the expected costs right away.",
                'consultation': "I'd be glad to discuss your project on a consultation call. What time works best for you?",
                'services': "At LazySoft we build chatbots, CRM systems, landing pages, data automation workflows and analytics dashboards. Tell me which direction you're exploring and I'll guide you through the next steps.",
                'general': "Happy to help! At LazySoft we design end-to-end IT solutions — chatbots, CRM, landing pages and data automations. Share what you're planning and I'll recommend the most effective path forward."
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
                
                # Якщо індексуємо KnowledgeSource — маршрутизуємо через reindex_object
                if model_class is KnowledgeSource:
                    for obj in objects:
                        try:
                            self.reindex_object(obj)
                            total_indexed += 1
                        except Exception as e:
                            logger.error(f"Помилка індексації KnowledgeSource {obj}: {e}")
                            continue
                else:
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
        
        # Спеціальна логіка для KnowledgeSource
        if isinstance(obj, KnowledgeSource):
            try:
                src_type = getattr(obj, 'source_type', 'manual')
                # Якщо джерело вказує на тип контенту, індексуємо відповідні моделі
                if src_type == 'service':
                    targets = ServiceCategory.objects.filter(is_active=True) if hasattr(ServiceCategory, 'is_active') else ServiceCategory.objects.all()
                    for target in targets:
                        for lang in languages:
                            self.embedding_service.create_embedding_for_object(target, lang)
                elif src_type == 'pricing':
                    # Індексувати ціни сервісів
                    try:
                        from pricing.models import ServicePricing
                        pricing_targets = ServicePricing.objects.filter(is_active=True)
                        for target in pricing_targets:
                            for lang in languages:
                                self.embedding_service.create_embedding_for_object(target, lang)
                    except Exception as e:
                        logger.error(f"Індексація pricing помилка: {e}")
                elif src_type == 'dialogs':
                    # Індексувати успішні діалоги як manual записи (вимагає контент у KnowledgeSource)
                    for lang in languages:
                        self.embedding_service.create_embedding_for_object(obj, lang)
                elif src_type == 'project':
                    for target in Project.objects.all():
                        for lang in languages:
                            self.embedding_service.create_embedding_for_object(target, lang)
                elif src_type == 'faq':
                    for target in FAQ.objects.all():
                        for lang in languages:
                            self.embedding_service.create_embedding_for_object(target, lang)
                else:
                    # manual: індексуємо сам KnowledgeSource
                    for lang in languages:
                        self.embedding_service.create_embedding_for_object(obj, lang)
                # Оновлюємо часову мітку
                try:
                    obj.last_embedding_update = timezone.now()
                    obj.save(update_fields=['last_embedding_update'])
                except Exception:
                    pass
                return
            except Exception as e:
                logger.error(f"Помилка маршрутизації KnowledgeSource {obj}: {e}")
                return

        # За замовчуванням: індексуємо сам об'єкт у всіх мовах
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