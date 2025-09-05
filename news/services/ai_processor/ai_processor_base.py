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
        self.preferred_model = getattr(settings, 'AI_PREFERRED_MODEL', 'gemini')  # 'openai' або 'gemini'
        self.backup_model = 'gemini' if self.preferred_model == 'openai' else 'openai'
        
        # Ініціалізація AI клієнтів
        self.openai_client = None
        self.gemini_model = None
        
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
            self.openai_client = OpenAI(
                api_key=api_key,
                organization=org,
                project=proj,
            )
            self.logger.info("OpenAI клієнт ініціалізовано (org=%s, project=%s)", org or "-", proj or "-")
        except Exception as e:
            self.openai_client = None
            self.logger.error("OpenAI клієнт не ініціалізувався: %s", e)
        
        # Google Gemini
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.logger.info(" Gemini клієнт ініціалізований")
            except Exception as e:
                self.logger.error(f"❌ Помилка ініціалізації Gemini: {e}")

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
        """Універсальний виклик AI з фолбеком: Gemini → GPT."""
        self.logger.info(f"[AI] Викликаємо {self.preferred_model} модель...")

        # 1) Основна модель
        try:
            if self.preferred_model == "gemini" and self.gemini_model:
                self.logger.info("[AI] Використовуємо Gemini...")
                resp = self._call_gemini(prompt, max_tokens)
                self.logger.info(f"[AI] Gemini відповів: {len(resp)} символів")
                return resp

            if self.preferred_model == "openai" and self.openai_client:
                self.logger.info("[AI] Використовуємо OpenAI...")
                resp = self._call_openai(prompt, max_tokens)
                self.logger.info(f"[AI] OpenAI відповів: {len(resp)} символів")
                return resp

        except Exception as e:
            msg = str(e)
            self.logger.warning(f"[WARNING] Основна модель ({self.preferred_model}) недоступна: {msg}")

            # Якщо це ліміт Gemini (429) — одразу перемикаємось на GPT
            if self.preferred_model == "gemini" and ("429" in msg or "quota" in msg.lower()):
                self.logger.warning("[WARNING] Gemini quota exceeded — switching to GPT-4.1")
                try:
                    return self._call_openai(prompt, max_tokens)
                except Exception as oe:
                    self.logger.error(f"❌ Фолбек на OpenAI теж впав: {oe}")

        # 2) Резервна модель (якщо налаштована)
        try:
            if getattr(self, "backup_model", None) == "openai" and self.openai_client:
                return self._call_openai(prompt, max_tokens)
            if getattr(self, "backup_model", None) == "gemini" and self.gemini_model:
                return self._call_gemini(prompt, max_tokens)
        except Exception as e:
            self.logger.error(f"❌ Резервна модель ({getattr(self, 'backup_model', None)}) недоступна: {e}")

        raise Exception("❌ Жодна AI модель недоступна")


    def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """Виклик OpenAI GPT (оновлена модель)."""
        # вибери свою дефолтну модель; 4o-mini дешевша, 4.1 – розумніша
        model = getattr(self, "openai_text_model", None) or "gpt-4.1"
        try:
            resp = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return resp.choices[0].message.content
        except Exception as e:
            # якщо раптом 429 у OpenAI — можна ще раз спробувати на дешевшій моделі
            msg = str(e)
            if "429" in msg or "rate" in msg.lower():
                self.logger.warning("[WARNING] OpenAI rate limit — fallback to gpt-4o-mini")
                resp = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7,
                )
                return resp.choices[0].message.content
            raise


    def _call_gemini(self, prompt: str, max_tokens: int) -> str:
        """Виклик Google Gemini з чітким логуванням помилок."""
        self.logger.info(f"[GEMINI] Відправляємо запит довжиною {len(prompt)} символів...")
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )
            if not getattr(response, "text", None):
                raise Exception("Gemini повернув пустий response.text")
            self.logger.info(f"[GEMINI] Успішна відповідь: {len(response.text)} символів")
            return response.text
        except Exception as e:
            self.logger.error(f"[GEMINI] Помилка: {e}")
            # Проброс виключення нагору — там спіймаємо 429 і перемкнемось на GPT
            raise


    def _calculate_cost(self, prompt: str, response: str) -> float:
        """Обчислює приблизну вартість AI запиту"""
        if self.preferred_model == 'openai':
            input_tokens = len(prompt.split()) * 1.3  # Приблизно
            output_tokens = len(response.split()) * 1.3
            cost = (input_tokens * 0.0015 + output_tokens * 0.002) / 1000
        else:  # Gemini
            tokens = (len(prompt) + len(response)) / 4  # Приблизно
            cost = tokens * 0.00025 / 1000
        
        return round(cost, 6)
    
    
    def get_processing_stats(self) -> Dict:
        """Повертає статистику обробки"""
        return self.stats.copy()