import os
import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Q, F
from datetime import datetime, timedelta
import logging
import re
from dataclasses import is_dataclass, asdict
from news.models import ProcessedArticle, RawArticle
from openai import OpenAI
from django.conf import settings

# AI imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Gemini видалено - використовуємо тільки OpenAI
GEMINI_AVAILABLE = False

from news.models import RawArticle, ProcessedArticle, AIProcessingLog, TranslationCache

logger = logging.getLogger(__name__)


@dataclass
class ProcessedContent:
    """Структура AI-обробленого контенту"""
    # Переклади
    title_en: str
    title_pl: str  
    title_uk: str
    
    summary_en: str
    summary_pl: str
    summary_uk: str
    
    business_insight_en: str
    business_insight_pl: str
    business_insight_uk: str
    
    local_context_en: str = ""
    local_context_pl: str = ""
    local_context_uk: str = ""
    
    key_takeaways_en: List[str] = None
    key_takeaways_pl: List[str] = None
    key_takeaways_uk: List[str] = None
    
    # Нові поля для детального аналізу
    interesting_facts_en: List[str] = None
    interesting_facts_pl: List[str] = None
    interesting_facts_uk: List[str] = None
    
    implementation_steps_en: List[str] = None
    implementation_steps_pl: List[str] = None
    implementation_steps_uk: List[str] = None
    
    # CTA
    cta_title_en: str = ""
    cta_title_pl: str = ""
    cta_title_uk: str = ""
    
    cta_description_en: str = ""
    cta_description_pl: str = ""
    cta_description_uk: str = ""
    
    cta_buttons: List[Dict] = None
    
    # AI image
    ai_image_prompt: str = ""
    ai_image_url: str = ""
    
    # Meta
    category_slug: str = "general"
    priority: int = 2
    ai_model_used: str = ""
    processing_time: float = 0
    cost: float = 0


class AINewsProcessor:
    """Головний AI процесор для новин"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # API ключі
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        # Налаштування AI - тільки OpenAI
        self.preferred_model = 'openai'
        self.backup_model = None
        
        # Ініціалізація AI клієнтів
        self.openai_client = None
        
        self._init_ai_clients()
        
        # Статистика
        self.stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'total_cost': 0,
            'total_time': 0
        }

    def _init_ai_clients(self):
        """Ініціалізація AI клієнтів"""
        # OpenAI
        org = getattr(settings, "OPENAI_ORG_ID", "") or None
        proj = getattr(settings, "OPENAI_PROJECT_ID", "") or None
        api_key = getattr(settings, "OPENAI_API_KEY", "")

        try:
            if api_key and OPENAI_AVAILABLE:
                self.openai_client = OpenAI(
                    api_key=api_key,
                    organization=org,
                    project=proj,
                )
                self.logger.info("OpenAI клієнт ініціалізовано (org=%s, project=%s)", org or "-", proj or "-")
            else:
                self.logger.warning("OpenAI API ключ не встановлено або бібліотека не доступна.")
        except Exception as e:
            self.openai_client = None
            self.logger.error("OpenAI клієнт не ініціалізувався: %s", e)
        
        # Gemini видалено - використовуємо тільки OpenAI

    def _safe_get_value(self, obj, key, default=""):
        """
        Безпечно дістає значення з dict/об'єкта.
        Підтримує obj.get(...), getattr(...), і повертає default якщо пусто.
        """
        if isinstance(obj, dict):
            val = obj.get(key, default)
        else:
            val = getattr(obj, key, default)
        return val if val is not None else default

    def _call_ai_model(self, prompt: str, max_tokens: int = 1000, **kwargs) -> str:
        """
        Уніфікований виклик до AI-провайдера (OpenAI).
        - Ігнорує/проковтує незнайомі kwargs (напр., response_format) якщо бекенд їх не підтримує.
        - Обмежує кількість токенів згідно з налаштуваннями.
        - Завжди повертає ТЕКСТ (str). Ексепшн піднімається вище для fallback-логіки.
        """
        from django.conf import settings  # локальний імпорт, якщо метод викликається рано під час ініціалізації

    # Налаштування
        temperature = float(getattr(settings, "AI_TEMPERATURE", 0.7))
        max_output_tokens = int(getattr(settings, "AI_MAX_TOKENS", 2000))
        model_name = getattr(settings, "AI_OPENAI_GENERATIVE_MODEL", "gpt-4o")

    # Фактичний ліміт вихідних токенів
        out_tokens = max(16, min(int(max_tokens or 0) or 0, max_output_tokens))

    # Діагностика виклику
        self.logger.info("[AI] Викликаємо OpenAI модель...")
        self.logger.info(f"[AI] Модель={model_name} | temperature={temperature} | max_tokens={out_tokens}")
        if kwargs:
            self.logger.debug(f"[AI] Додаткові параметри: {list(kwargs.keys())}")

        if not getattr(self, "openai_client", None):
        # Немає ініціалізованого клієнта — це критична ситуація, нехай обробляється вище
            raise RuntimeError("OpenAI клієнт не ініціалізований")

    # Спроба №1: з усіма kwargs (наприклад, response_format={"type":"json_object"})
        try:
            resp = self._call_openai(prompt, out_tokens, temperature, **kwargs)
            if resp is None:
                self.logger.warning("[AI] Порожня відповідь (None) від _call_openai у спробі №1.")
                resp = ""
            text = resp if isinstance(resp, str) else str(resp)
            self.logger.info(f"[AI] OpenAI відповів (спроба №1): {len(text)} символів")
            if len(text) < 64:
                self.logger.debug(f"[AI RAW <=64] {text!r}")
            return text

        except TypeError as te:
        # Напр., бекенд не підтримує response_format або інші kwargs
            self.logger.warning(f"[AI] _call_openai не підтримує деякі kwargs ({list(kwargs.keys())}). "
                                f"Повторюю без них. Деталі: {te}")

    # Спроба №2: без додаткових kwargs — максимально сумісно
        try:
            resp = self._call_openai(prompt, out_tokens, temperature)
            if resp is None:
                self.logger.warning("[AI] Порожня відповідь (None) від _call_openai у спробі №2.")
                resp = ""
            text = resp if isinstance(resp, str) else str(resp)
            self.logger.info(f"[AI] OpenAI відповів (спроба №2): {len(text)} символів")
            if len(text) < 64:
                self.logger.debug(f"[AI RAW <=64] {text!r}")
            return text

        except Exception as e:
            # Інші помилки — піднімаємо вище, щоб спрацював fallback
            self.logger.exception(f"[AI] Критична помилка виклику моделі: {e}")
            raise



    def _call_openai(self, prompt: str, max_tokens: int, temperature: float, is_fallback: bool = False, **kwargs) -> str:
        """Виклик OpenAI GPT (оновлена модель) з підтримкою kwargs."""
        model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL', 'gpt-4o')
        if is_fallback:
            model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL_FALLBACK', 'gpt-4o-mini')

        self.logger.info(f"[OPENAI] Відправляємо запит до моделі {model_name} довжиною {len(prompt)} символів...")

        # Формуємо параметри для API виклику
        api_params = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Додаємо response_format якщо він переданий і модель його підтримує
        if "response_format" in kwargs:
            try:
                api_params["response_format"] = kwargs["response_format"]
                self.logger.debug(f"[OPENAI] Додано response_format: {kwargs['response_format']}")
            except Exception as e:
                self.logger.warning(f"[OPENAI] Не вдалося додати response_format: {e}")

        try:
            resp = self.openai_client.chat.completions.create(**api_params)
            self.logger.info(f"[OPENAI] Успішна відповідь від {model_name}: {len(resp.choices[0].message.content)} символів")
            return resp.choices[0].message.content
        except Exception as e:
            self.logger.error(f"[OPENAI] Помилка від {model_name}: {e}")
            raise


# Метод _call_gemini видалено - використовуємо тільки OpenAI


    def _calculate_cost(self, prompt: str, response: str) -> float:
        """Обчислює приблизну вартість AI запиту (тільки OpenAI)"""
        # Для OpenAI використовуємо токенізовану вартість (приблизно)
        input_tokens = len(prompt.split()) / 0.75  # Приблизно, щоб врахувати різницю в токенізації
        output_tokens = len(response.split()) / 0.75
        
        # Вартість залежить від моделі
        # gpt-4o: input 5$/M, output 15$/M
        # gpt-4o-mini: input 0.15$/M, output 0.6$/M
        
        model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL', 'gpt-4o')

        if 'gpt-4o-mini' in model_name:
            cost = (input_tokens * 0.15 + output_tokens * 0.6) / 1_000_000
        elif 'gpt-4o' in model_name:
            cost = (input_tokens * 5 + output_tokens * 15) / 1_000_000
        else: # Дефолт, якщо модель не впізнана
            cost = (input_tokens * 1 + output_tokens * 2) / 1_000_000 # Дуже приблизно
        
        return round(cost, 6)
    
    
    def get_processing_stats(self) -> Dict:
        """Повертає статистику обробки"""
        return self.stats.copy()
