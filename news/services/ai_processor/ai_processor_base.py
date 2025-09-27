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

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
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
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        # Налаштування AI
        self.preferred_model = getattr(settings, 'AI_PREFERRED_MODEL', 'openai')  # 'openai' або 'gemini'
        self.backup_model = getattr(settings, 'AI_BACKUP_MODEL', 'gemini')
        
        # Ініціалізація AI клієнтів
        self.openai_client = None
        self.gemini_model = None
        self.gemini_embedding_model = None # Додаємо для ембеддінгів
        
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
        
        # Google Gemini
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(getattr(settings, 'AI_GEMINI_GENERATIVE_MODEL', 'gemini-1.5-flash'))
                self.logger.info(" Gemini клієнт ініціалізований")
            except Exception as e:
                self.logger.error(f"❌ Помилка ініціалізації Gemini: {e}")
        else:
            self.logger.warning("Gemini API ключ не встановлено або бібліотека не доступна.")

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

    def _call_ai_model(self, prompt: str, max_tokens: int = 1000) -> str:
        """Універсальний виклик AI з фолбеком: Preferred → Backup → Exception."""
        self.logger.info(f"[AI] Викликаємо {self.preferred_model} модель...")

        # Завантажуємо налаштування температури з settings.py
        temperature = getattr(settings, 'AI_TEMPERATURE', 0.7)
        max_output_tokens = getattr(settings, 'AI_MAX_TOKENS', 2000)

        # 1) Основна модель
        try:
            if self.preferred_model == "gemini" and self.gemini_model:
                self.logger.info(f"[AI] Використовуємо Gemini ({getattr(settings, 'AI_GEMINI_GENERATIVE_MODEL', 'gemini-1.5-flash')})...")
                resp = self._call_gemini(prompt, max_output_tokens, temperature)
                self.logger.info(f"[AI] Gemini відповів: {len(resp)} символів")
                return resp

            if self.preferred_model == "openai" and self.openai_client:
                self.logger.info(f"[AI] Використовуємо OpenAI ({getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL', 'gpt-4o')})...")
                resp = self._call_openai(prompt, max_output_tokens, temperature)
                self.logger.info(f"[AI] OpenAI відповів: {len(resp)} символів")
                return resp

        except Exception as e:
            msg = str(e)
            self.logger.warning(f"[WARNING] Основна модель ({self.preferred_model}) недоступна: {msg}")

        # 2) Резервна модель (якщо налаштована)
        if self.backup_model:
            self.logger.info(f"[AI] Спробуємо резервну модель ({self.backup_model})...")
            try:
                if self.backup_model == "openai" and self.openai_client:
                    self.logger.info(f"[AI] Використовуємо OpenAI Fallback ({getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL_FALLBACK', 'gpt-4o-mini')})...")
                    return self._call_openai(prompt, max_output_tokens, temperature, is_fallback=True)
                if self.backup_model == "gemini" and self.gemini_model:
                    self.logger.info(f"[AI] Використовуємо Gemini Fallback ({getattr(settings, 'AI_GEMINI_GENERATIVE_MODEL', 'gemini-1.5-flash')})...")
                    return self._call_gemini(prompt, max_output_tokens, temperature)
            except Exception as e:
                self.logger.error(f"❌ Резервна модель ({self.backup_model}) теж недоступна: {e}")

        raise Exception("❌ Жодна AI модель недоступна")


    def _call_openai(self, prompt: str, max_tokens: int, temperature: float, is_fallback: bool = False) -> str:
        """Виклик OpenAI GPT (оновлена модель)."""
        model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL', 'gpt-4o')
        if is_fallback:
            model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL_FALLBACK', 'gpt-4o-mini')
        
        self.logger.info(f"[OPENAI] Відправляємо запит до моделі {model_name} довжиною {len(prompt)} символів...")
        try:
            resp = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            self.logger.info(f"[OPENAI] Успішна відповідь від {model_name}: {len(resp.choices[0].message.content)} символів")
            return resp.choices[0].message.content
        except Exception as e:
            self.logger.error(f"[OPENAI] Помилка від {model_name}: {e}")
            raise


    def _call_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Виклик Google Gemini з чітким логуванням помилок."""
        model_name = getattr(settings, 'AI_GEMINI_GENERATIVE_MODEL', 'gemini-1.5-flash')
        self.logger.info(f"[GEMINI] Відправляємо запит до моделі {model_name} довжиною {len(prompt)} символів...")
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            if not getattr(response, "text", None):
                raise Exception("Gemini повернув пустий response.text")
            self.logger.info(f"[GEMINI] Успішна відповідь від {model_name}: {len(response.text)} символів")
            return response.text
        except Exception as e:
            self.logger.error(f"[GEMINI] Помилка від {model_name}: {e}")
            raise


    def _calculate_cost(self, prompt: str, response: str) -> float:
        """Обчислює приблизну вартість AI запиту"""
        model_used = "openai" if self.openai_client else "gemini"
        if model_used == 'openai':
            # Для OpenAI використовуємо токенізовану вартість (приблизно)
            input_tokens = len(prompt.split()) / 0.75  # Приблизно, щоб врахувати різницю в токенізації
            output_tokens = len(response.split()) / 0.75
            
            # Вартість залежить від моделі, але для простоти візьмемо середню
            # Ціни OpenAI можуть бути дуже різними, тому це приблизно
            # gpt-4o: input 5$/M, output 15$/M
            # gpt-4o-mini: input 0.15$/M, output 0.6$/M
            
            model_name = self.preferred_model
            if self.preferred_model == 'openai':
                model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL', 'gpt-4o')
            if self.backup_model == 'openai' and not self.openai_client:
                model_name = getattr(settings, 'AI_OPENAI_GENERATIVE_MODEL_FALLBACK', 'gpt-4o-mini')

            if 'gpt-4o-mini' in model_name:
                cost = (input_tokens * 0.15 + output_tokens * 0.6) / 1_000_000
            elif 'gpt-4o' in model_name:
                cost = (input_tokens * 5 + output_tokens * 15) / 1_000_000
            else: # Дефолт, якщо модель не впізнана
                cost = (input_tokens * 1 + output_tokens * 2) / 1_000_000 # Дуже приблизно
        else:  # Gemini
            # Gemini ціни: input 0.125$/M, output 0.375$/M (для flash)
            tokens = (len(prompt) + len(response)) / 4  # Приблизно
            cost = (tokens * 0.125 + tokens * 0.375) / 1_000_000
        
        return round(cost, 6)
    
    
    def get_processing_stats(self) -> Dict:
        """Повертає статистику обробки"""
        return self.stats.copy()