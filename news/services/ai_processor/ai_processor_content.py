import json
import logging
from typing import Dict
from .ai_processor_base import AINewsProcessor
from news.models import RawArticle

logger = logging.getLogger(__name__)


class AIContentProcessor(AINewsProcessor):
    """Модуль для створення тримовного контенту"""

    def _categorize_article(self, raw_article: RawArticle) -> Dict:
        """AI категоризація статті"""
        
        categories = {
            'ai': 'artificial intelligence, machine learning, neural networks, AI models, automation AI',
            'automation': 'business automation, RPA, workflow automation, process optimization, zapier',
            'crm': 'customer relationship management, sales automation, CRM systems, customer service',
            'seo': 'search engine optimization, digital marketing, SEO tools, search rankings, Google',
            'social': 'social media marketing, Facebook, Instagram, Twitter, social media automation',
            'chatbots': 'chatbots, conversational AI, virtual assistants, customer support bots',
            'ecommerce': 'online store, e-commerce platforms, Shopify, online retail, digital commerce',
            'fintech': 'financial technology, payments, cryptocurrency, digital banking, blockchain',
            'corporate': 'enterprise technology, business technology, corporate news, company updates',
            'general': 'technology news, tech industry, software development, programming'
        }
        
        # Простий AI промпт для категоризації
        content_for_analysis = f"{raw_article.title} {raw_article.summary}"
        
        prompt = f"""
        Analyze this article and determine the most appropriate category:
        
        Article: {content_for_analysis[:500]}
        
        Categories: {json.dumps(categories)}
        
        Respond with just the category slug (e.g., "ai", "automation", etc.)
        """
        
        try:
            category_slug = self._call_ai_model(prompt, max_tokens=10).strip().lower()
            
            # Валідація категорії
            if category_slug not in categories:
                category_slug = 'general'
            
            # Визначаємо пріоритет
            priority = 2  # Середній за замовчанням
            if any(word in content_for_analysis.lower() for word in ['breaking', 'urgent', 'major', 'launches']):
                priority = 3  # Високий
            elif 'google' in content_for_analysis.lower() or 'microsoft' in content_for_analysis.lower():
                priority = 3  # Високий для великих компаній
                
            return {
                'category': category_slug,
                'priority': priority,
                'keywords': categories[category_slug].split(', ')
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Помилка категоризації: {e}")
            return {'category': 'general', 'priority': 2, 'keywords': []}
        
    def _clip_to_range(self, text: str, min_len: int = 900, max_len: int = 1200) -> str:
        """Обрізає текст до діапазону символів із м'яким зрізом по крапці."""
        if not text:
            return ""
        t = text.strip()
        if len(t) > max_len:
            # спробуємо обрізати по закінченню речення
            cut = t.rfind(". ", 0, max_len)
            if cut >= min_len:
                t = t[:cut+1]
            else:
                t = t[:max_len]
        return t

    def _normalize_lengths(self, content_data: Dict) -> Dict:
        """Забезпечує довжину 900–1200 символів для summary_*."""
        for lang in ["en", "uk", "pl"]:
            key = f"summary_{lang}"
            content_data[key] = self._clip_to_range(content_data.get(key, ""), 900, 1200)
        return content_data
    
    def _clean_json_response(self, response: str) -> str:
        """Очищає JSON відповідь від markdown блоків та зайвого тексту"""
        
        # Видаляємо markdown блоки
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        
        # Очищаємо пробіли
        response = response.strip()
        
        # ЗНАХОДИМО ТІЛЬКИ JSON ЧАСТИНУ
        try:
            # Шукаємо початок JSON
            start = response.find('{')
            if start == -1:
                return response
                
            # Рахуємо дужки щоб знайти кінець JSON
            brace_count = 0
            end = start
            
            for i, char in enumerate(response[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            # Повертаємо тільки JSON частину
            json_part = response[start:end]
            return json_part
            
        except Exception as e:
            # Якщо не вдалося парсити, повертаємо як є
            return response

    def _create_multilingual_content(self, raw_article: RawArticle, category_info: Dict) -> dict:
        """Створює тримовний ОРИГІНАЛЬНИЙ бізнес-аналіз з RSS (~1000–1200 символів)."""
        original_title = raw_article.title or ""
        rss_snippet = (raw_article.summary or raw_article.content or "")[:1200]
        category = category_info["category"]

        main_prompt = f"""
        You are LAZYSOFT's tech/business editor. Write ORIGINAL, NON-COPIED analysis
        for SMB readers based on the topic below. Use general knowledge; avoid unverifiable claims.
        Do NOT translate the RSS; produce a fresh piece from LAZYSOFT perspective.

        TOPIC TITLE: {original_title}
        RSS SNIPPET (context only): {rss_snippet}
        CATEGORY: {category}

        REQUIREMENTS:
        - Three languages: EN, UK, PL.
        - Each "summary_*" must be 1000–1200 characters (roughly ~1100), readable, with 2–3 concrete use-cases and a mini-conclusion.
        - Tone: practical, concise, business impact for SMB in Europe.
        - NO bullet lists (continuous prose). NO quotes from source. No URLs inside text.
        - Provide catchy business-focused titles per language (not clickbait).
        - Keep facts generic/safe; if specifics are unknown, generalize (no hallucinations).

        OUTPUT JSON ONLY:
        {{
            "title_en": "...",
            "title_uk": "...",
            "title_pl": "...",
            "summary_en": "... (1000-1200 chars)",
            "summary_uk": "... (1000-1200 chars)",
            "summary_pl": "... (1000-1200 chars)",
            "insight_en": "1-2 sentences with actionable angle",
            "insight_uk": "1-2 речення з практичним кутом",
            "insight_pl": "1-2 zdania z praktycznym kątem"
        }}
        """

        try:
            self.logger.info("[AI] Генеруємо оригінальний 3-мовний контент ~1100 символів...")
            response = self._call_ai_model(main_prompt, max_tokens=1600)
            cleaned = self._clean_json_response(response)
            content_data = json.loads(cleaned)
        except Exception as e:
            self.logger.error(f"[AI] Помилка JSON: {e}")
            content_data = self._create_fallback_content_dict(raw_article, category_info)

        # Нормалізація довжин summary
        content_data = self._normalize_lengths(content_data)

        # SEO / CTA / cost
        seo = self._generate_seo_metadata(content_data, category)
        cta_buttons = self._generate_cta_buttons(category)
        cost = self._calculate_cost(main_prompt, json.dumps(content_data))

        # Промпт для зображення (як і раніше — стиль залишаємо брендовий)
        title_en = content_data.get("title_en", original_title)
        style = ("Minimalistic flat illustration, neon accents, glassmorphism, "
                "modern tech magazine cover, trending on Dribbble")

        return {
            "title_en": title_en,
            "title_pl": content_data.get("title_pl", original_title),
            "title_uk": content_data.get("title_uk", original_title),

            # тут тепер лежить наш ОРИГІНАЛЬНИЙ 1000–1200 симв. текст
            "summary_en": content_data.get("summary_en", rss_snippet),
            "summary_pl": content_data.get("summary_pl", rss_snippet),
            "summary_uk": content_data.get("summary_uk", rss_snippet),

            "business_insight_en": content_data.get("insight_en", ""),
            "business_insight_pl": content_data.get("insight_pl", ""),
            "business_insight_uk": content_data.get("insight_uk", ""),

            "category_slug": category,
            "priority": category_info.get("priority", 2),

            "ai_image_prompt_en": f"Cover about: {title_en}. {style}",
            "ai_model_used": self.preferred_model,
            "processing_time": 0,
            "cost": cost,
            **seo,
            "cta_buttons": cta_buttons
        }


    def _create_fallback_content_dict(self, raw_article: RawArticle, category_info: Dict) -> dict:
        """Створює fallback контент якщо AI недоступний"""
        title = raw_article.title or ""
        summary_src = raw_article.summary or raw_article.content or ""
        summary = summary_src[:160]

        return {
            "title_en": title, "title_pl": title, "title_uk": title,
            "summary_en": summary, "summary_pl": summary, "summary_uk": summary,

            "business_insight_en": "This technology update may impact European businesses.",
            "business_insight_pl": "Ta aktualizacja technologiczna może wpłynąć na europejskie firmy.",
            "business_insight_uk": "Це технологічне оновлення може вплинути на європейський бізнес.",

            "key_takeaways_en": ["Stay updated with latest tech trends"],
            "key_takeaways_pl": ["Bądź na bieżąco z najnowszymi trendami technologicznymi"],
            "key_takeaways_uk": ["Залишайтесь в курсі останніх технологічних трендів"],

            # CTA – не пусті
            "cta_title_en": "Get Expert Analysis",
            "cta_title_pl": "Otrzymaj ekspercką analizę",
            "cta_title_uk": "Отримати експертний аналіз",
            "cta_description_en": "Contact us for personalized business consultation",
            "cta_description_pl": "Skontaktuj się z nami w sprawie spersonalizowanej konsultacji biznesowej",
            "cta_description_uk": "Звʼяжіться з нами для персоналізованої бізнес-консультації",
            "cta_buttons": self._generate_cta_buttons(category_info["category"]),

            # Промпти з опису
            "ai_image_prompt_en": title,
            "ai_image_prompt_uk": title,
            "ai_image_prompt_pl": title,
            

            # SEO – не пусті
            "meta_title_en": title[:60], "meta_title_pl": title[:60], "meta_title_uk": title[:60],
            "meta_description_en": summary[:160], "meta_description_pl": summary[:160], "meta_description_uk": summary[:160],

            "category_slug": category_info["category"],
            "priority": category_info["priority"],
            "ai_model_used": "fallback",
            "cost": 0.0,
        }