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
        
    def _clip_to_range(self, text: str, min_len: int = 2000, max_len: int = 3000) -> str:
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
        """Забезпечує довжину 2000–3000 символів для summary_*."""
        for lang in ["en", "uk", "pl"]:
            key = f"summary_{lang}"
            content_data[key] = self._clip_to_range(content_data.get(key, ""), 2000, 3000)
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
        # Використовуємо збагачений контент (FiveFilters вже спрацював)
        full_content = raw_article.content or raw_article.summary or ""
        content_for_ai = full_content[:2000]  # Збільшуємо ліміт для кращого AI аналізу
        category = category_info["category"]

        main_prompt = f"""
        You are LAZYSOFT's tech/business editor. Create COMPREHENSIVE business analysis 
        based on the FULL ARTICLE CONTENT below for SMB readers in Europe.

        ORIGINAL TITLE: {original_title}
        FULL ARTICLE CONTENT: {content_for_ai}
        CATEGORY: {category}

        IMPORTANT: You have FULL article content, not just RSS snippet. 
        Use this rich information to create detailed, valuable business insights with SEO-optimized length.

        REQUIREMENTS:
        - Three languages: EN, UK, PL.
        - Each "summary_*" must be 2000–3000 characters for better SEO performance.
        - Extract specific facts, numbers, and actionable insights from the content.
        - You CAN include relevant quotes from the original article (use quotation marks).
        - Focus on business impact for European SMBs with concrete examples.
        - Create comprehensive analysis with multiple paragraphs and detailed explanations.
        - Use the full context to provide deeper insights than typical RSS summaries.
        - Include specific data points, statistics, and concrete business implications.
        - Structure content with clear introduction, main analysis, and actionable conclusions.

        OUTPUT JSON ONLY:
        {{
            "title_en": "Business-focused title based on article insights",
            "title_uk": "Бізнес-орієнтований заголовок",
            "title_pl": "Tytuł skoncentrowany na biznesie",
            "summary_en": "Comprehensive analysis using full article content (2000-3000 chars)",
            "summary_uk": "Комплексний аналіз на основі повного контенту (2000-3000 символів)",
            "summary_pl": "Kompleksowa analiza oparta na pełnej treści (2000-3000 znaków)",
            "insight_en": "Specific actionable business insight from article",
            "insight_uk": "Конкретний практичний бізнес-інсайт зі статті",
            "insight_pl": "Konkretny praktyczny biznesowy wgląd z artykułu",
            "business_opportunities_en": "Specific business opportunities for European SMBs (300-500 chars)",
            "business_opportunities_uk": "Конкретні бізнес-можливості для європейських МСП (300-500 символів)",
            "business_opportunities_pl": "Konkretne możliwości biznesowe dla europejskich MŚP (300-500 znaków)",
            "lazysoft_recommendations_en": "LAZYSOFT automation recommendations based on article insights (300-500 chars)",
            "lazysoft_recommendations_uk": "Рекомендації LAZYSOFT з автоматизації на основі інсайтів статті (300-500 символів)",
            "lazysoft_recommendations_pl": "Rekomendacje LAZYSOFT dotyczące automatyzacji na podstawie wglądów z artykułu (300-500 znaków)"
        }}
        """

        try:
            self.logger.info("[AI] Генеруємо оригінальний 3-мовний контент ~2500 символів...")
            response = self._call_ai_model(main_prompt, max_tokens=3000)
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

        title_en = content_data.get("title_en", original_title)

        return {
            "title_en": title_en,
            "title_pl": content_data.get("title_pl", original_title),
            "title_uk": content_data.get("title_uk", original_title),

            # тут тепер лежить наш ОРИГІНАЛЬНИЙ 2000–3000 симв. текст
            "summary_en": content_data.get("summary_en", content_for_ai[:2500]),
            "summary_pl": content_data.get("summary_pl", content_for_ai[:2500]),
            "summary_uk": content_data.get("summary_uk", content_for_ai[:2500]),

            "business_insight_en": content_data.get("insight_en", ""),
            "business_insight_pl": content_data.get("insight_pl", ""),
            "business_insight_uk": content_data.get("insight_uk", ""),

            "business_opportunities_en": content_data.get("business_opportunities_en", ""),
            "business_opportunities_pl": content_data.get("business_opportunities_pl", ""),
            "business_opportunities_uk": content_data.get("business_opportunities_uk", ""),

            "lazysoft_recommendations_en": content_data.get("lazysoft_recommendations_en", ""),
            "lazysoft_recommendations_pl": content_data.get("lazysoft_recommendations_pl", ""),
            "lazysoft_recommendations_uk": content_data.get("lazysoft_recommendations_uk", ""),

            "category_slug": category,
            "priority": category_info.get("priority", 2),

            "ai_model_used": self.preferred_model,
            "processing_time": 0,
            "cost": cost,
            **seo,
            "cta_buttons": cta_buttons
        }
        
        # Логування для діагностики
        self.logger.info(f"[DEBUG] Business opportunities EN: {bool(result.get('business_opportunities_en'))}")
        self.logger.info(f"[DEBUG] LAZYSOFT recommendations EN: {bool(result.get('lazysoft_recommendations_en'))}")
        
        return result


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