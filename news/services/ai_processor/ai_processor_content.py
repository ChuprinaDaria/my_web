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
        
        Article: {content_for_analysis[:2000]}
        
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

    def _extract_main_topic(self, title: str) -> str:
        """Витягує основну тему з заголовка для fallback заголовків"""
        if not title:
            return "Technology"
            
        # Очищаємо заголовок від зайвих символів
        clean_title = title.strip()
        
        # Витягуємо ключові слова
        tech_keywords = {
            'ai': 'AI', 'artificial intelligence': 'AI', 'machine learning': 'ML',
            'automation': 'Automation', 'docker': 'Docker', 'kubernetes': 'Kubernetes',
            'google': 'Google Tech', 'microsoft': 'Microsoft Tech', 'apple': 'Apple Tech',
            'openai': 'OpenAI', 'chatgpt': 'ChatGPT', 'blockchain': 'Blockchain',
            'cryptocurrency': 'Crypto', 'fintech': 'FinTech', 'startup': 'Startup',
            'security': 'Security', 'privacy': 'Privacy', 'cloud': 'Cloud',
            'api': 'API', 'software': 'Software', 'development': 'Development'
        }
        
        title_lower = clean_title.lower()
        
        # Шукаємо ключові слова
        for keyword, topic in tech_keywords.items():
            if keyword in title_lower:
                return topic
                
        # Якщо не знайшли ключових слів, беремо перші слова
        words = clean_title.split()[:3]  # Перші 3 слова
        if words:
            return ' '.join(words)
            
        return "Technology"

    def _normalize_lengths(self, content_data: Dict) -> Dict:
        """Забезпечує довжину 2000–3000 символів для summary_*."""
        for lang in ["en", "uk", "pl"]:
            key = f"summary_{lang}"
            content_data[key] = self._clip_to_range(content_data.get(key, ""), 2000, 3000)
        return content_data
    
    def _clean_json_response(self, response: str) -> str:
        """Очищає JSON відповідь від markdown блоків та зайвого тексту"""
        
        if not response or not response.strip():
            return "{}"
        
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
                self.logger.warning(f"[JSON] Не знайдено початок JSON в відповіді: {response[:200]}...")
                return "{}"
                
            # Рахуємо дужки щоб знайти кінець JSON
            brace_count = 0
            end = start
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
            
            # Повертаємо тільки JSON частину
            json_part = response[start:end]
            
            # Перевіряємо чи це валідний JSON
            try:
                parsed = json.loads(json_part)
                self.logger.info(f"[JSON] Успішно розпарсено JSON з {len(parsed)} полями")
                return json_part
            except json.JSONDecodeError as e:
                self.logger.warning(f"[JSON] Невалідний JSON: {e}")
                self.logger.warning(f"[JSON] Проблемна частина: {json_part[-200:]}")
                
                # Спробуємо виправити JSON, обрізавши до останнього валідного поля
                try:
                    # Шукаємо останній валідний закриваючий дужки
                    last_valid_brace = json_part.rfind('}')
                    if last_valid_brace > 0:
                        # Додаємо закриваючу дужку
                        fixed_json = json_part[:last_valid_brace + 1]
                        parsed = json.loads(fixed_json)
                        self.logger.info(f"[JSON] Виправлено JSON, обрізано до {len(parsed)} полів")
                        return fixed_json
                except:
                    pass
                
                # Якщо JSON зовсім невалідний, спробуємо знайти хоча б частину
                try:
                    # Шукаємо перший валідний JSON об'єкт
                    start = json_part.find('{')
                    if start >= 0:
                        # Шукаємо останню закриваючу дужку
                        last_brace = json_part.rfind('}')
                        if last_brace > start:
                            partial_json = json_part[start:last_brace + 1]
                            # Додаємо закриваючі дужки для недописаних полів
                            if not partial_json.strip().endswith('}'):
                                partial_json += '}'
                            parsed = json.loads(partial_json)
                            self.logger.info(f"[JSON] Відновлено частковий JSON з {len(parsed)} полями")
                            return partial_json
                except:
                    pass
                
                # Остання спроба - створити мінімальний JSON з тим що є
                try:
                    # Шукаємо хоча б заголовки
                    title_en_match = json_part.find('"title_en"')
                    if title_en_match > 0:
                        # Шукаємо значення title_en
                        start_quote = json_part.find('"', title_en_match + 10)
                        end_quote = json_part.find('"', start_quote + 1)
                        if start_quote > 0 and end_quote > start_quote:
                            title_en = json_part[start_quote + 1:end_quote]
                            
                            # Створюємо мінімальний JSON
                            minimal_json = f'{{"title_en": "{title_en}", "title_uk": "{title_en}", "title_pl": "{title_en}"}}'
                            parsed = json.loads(minimal_json)
                            self.logger.info(f"[JSON] Створено мінімальний JSON з {len(parsed)} полями")
                            return minimal_json
                except:
                    pass
                
                return "{}"
            
        except Exception as e:
            self.logger.error(f"[JSON] Помилка парсингу JSON: {e}")
            return "{}"

    def _create_multilingual_content(self, raw_article: RawArticle, category_info: Dict) -> dict:
        """Створює тримовний ОРИГІНАЛЬНИЙ бізнес-аналіз з RSS (~1000–1200 символів)."""
        original_title = raw_article.title or ""
        # Використовуємо збагачений контент (FiveFilters вже спрацював)
        full_content = raw_article.content or raw_article.summary or ""
        content_for_ai = full_content[:2000]  # Збільшуємо ліміт для кращого AI аналізу
        category = category_info["category"]

        # Підготовуємо дані для промпту
        source_name = raw_article.source.name if raw_article.source else "Unknown Source"
        original_url = raw_article.original_url or ""
        
        main_prompt = f"""
        You are LAZYSOFT's tech/business editor. Create business analysis for European SMBs.

        ORIGINAL TITLE: {original_title}
        ARTICLE CONTENT: {content_for_ai[:1200]}
        CATEGORY: {category}
        SOURCE: {source_name}
        ORIGINAL_URL: {original_url}

        CRITICAL CONCEPT: You are creating LAZYSOFT's ORIGINAL CONTENT - our thoughts, analysis, and opinions about the article.
        This is NOT a translation or republication. This is LAZYSOFT's unique business perspective.
        
        REQUIREMENTS:
        - Create UNIQUE business-focused titles (NOT translations of original)
        - Write comprehensive LAZYSOFT analysis (2000-3000 chars) with our insights
        - Always acknowledge the source and provide link to original
        - Mix different intro/outro patterns for variety
        - Focus on business impact for European SMBs
        
        TONE VARIETY: Mix professional, analytical, conversational, and expert tones across different articles.
        STYLE DIVERSITY: Alternate between formal business language and approachable explanations.

        CRITICAL INSTRUCTIONS:
        - ALWAYS start summary with one of the provided intro patterns (use "наші думки", "наш аналіз", etc.)
        - Replace SOURCE with: {source_name}
        - Replace ORIGINAL_URL with: {original_url}  
        - Replace [topic] and [temat] with the actual topic from the article
        - MUST include LAZYSOFT perspective phrases like "наші думки", "наша точка зору", "команда LAZYSOFT"
        - ALWAYS end summary with source link

        IMPORTANT: Respond with ONLY valid JSON. No explanations, no markdown, no extra text.
        
        {{
            "title_en": "Create unique business title (different from original)",
            "title_uk": "Створи унікальний бізнес-заголовок (відмінний від оригіналу)",
            "title_pl": "Stwórz unikalny tytuł biznesowy (różny od oryginału)",
            
            "summary_en": "RANDOM intro pattern: 'Recently SOURCE published an interesting article about [topic]. Here are our thoughts:' OR 'Found a very interesting piece in SOURCE about [topic]. Sharing our insights:' OR 'LAZYSOFT team analyzed SOURCE publication. Our conclusions:' OR 'SOURCE talks about [topic] - we add our context:' OR 'Noticed an interesting trend in SOURCE article. Breaking it down:' OR 'Analyzing fresh publication from SOURCE:' OR 'Studied SOURCE article and have something to say:' + comprehensive LAZYSOFT analysis (2000-3000 chars) + RANDOM outro: 'Source: ORIGINAL_URL' OR 'Full article: ORIGINAL_URL' OR 'Read more: ORIGINAL_URL' OR 'Original piece: ORIGINAL_URL'",
            
            "summary_uk": "ОБОВ'ЯЗКОВО почни з ОДНОГО з цих шаблонів: 'Нещодавно SOURCE опублікував цікаву статтю про [тема]. Ось наші думки:' АБО 'Знайшли дуже цікавий матеріал у SOURCE про [тема]. Ділимося інсайтами:' АБО 'Команда LAZYSOFT проаналізувала публікацію SOURCE. Наші висновки:' АБО 'SOURCE розповідає про [тема] - ми додаємо свій контекст:' АБО 'Помітили цікаву тенденцію у статті SOURCE. Розбираємося:' АБО 'Аналізуємо свіжу публікацію SOURCE:' АБО 'Вивчили статтю SOURCE і маємо що сказати:' АБО 'Цікавий кейс від SOURCE. Розбираємо детально:' АБО 'У SOURCE з\'явився матеріал про [тема]. Що ми про це думаємо:' АБО 'SOURCE ділиться інформацією про [тема]. Наша точка зору:' + комплексний аналіз LAZYSOFT (2000-3000 символів) + ОБОВ'ЯЗКОВО закінчи з: 'Джерело: ORIGINAL_URL' АБО 'Повний матеріал: ORIGINAL_URL' АБО 'Детальніше в оригіналі: ORIGINAL_URL' АБО 'Оригінальна стаття: ORIGINAL_URL' АБО 'Більше подробиць: ORIGINAL_URL' АБО 'Повна версія тут: ORIGINAL_URL'",
            
            "summary_pl": "LOSOWE intro: 'Niedawno SOURCE opublikował ciekawy artykuł o [temat]. Oto nasze przemyślenia:' LUB 'Znaleźliśmy bardzo ciekawy materiał w SOURCE o [temat]. Dzielimy się spostrzeżeniami:' LUB 'Zespół LAZYSOFT przeanalizował publikację SOURCE. Nasze wnioski:' LUB 'SOURCE mówi o [temat] - dodajemy nasz kontekst:' LUB 'Zauważyliśmy ciekawy trend w artykule SOURCE. Analizujemy:' LUB 'Analizujemy świeżą publikację SOURCE:' LUB 'Przestudiowaliśmy artykuł SOURCE i mamy co powiedzieć:' + kompleksowa analiza LAZYSOFT (2000-3000 znaków) + LOSOWE outro: 'Źródło: ORIGINAL_URL' LUB 'Pełny artykuł: ORIGINAL_URL' LUB 'Więcej szczegółów: ORIGINAL_URL' LUB 'Oryginalny materiał: ORIGINAL_URL'",
            
            "business_insight_en": "RANDOM start: 'Key business insight:' OR 'Most important for SMB:' OR 'Main conclusion:' OR 'Interesting point:' OR 'Critical takeaway:' OR 'Business impact:' + specific actionable business insight",
            
            "business_insight_uk": "ВИПАДКОВИЙ початок: 'Ключовий інсайт для бізнесу:' АБО 'Найважливіше для МСП:' АБО 'Головний висновок:' АБО 'Цікавий момент:' АБО 'Критичний висновок:' АБО 'Вплив на бізнес:' АБО 'Практичний інсайт:' АБО 'Бізнес-можливість:' + конкретний практичний бізнес-інсайт зі статті",
            
            "business_insight_pl": "LOSOWY początek: 'Kluczowy wgląd biznesowy:' LUB 'Najważniejsze dla MŚP:' LUB 'Główny wniosek:' LUB 'Ciekawy punkt:' LUB 'Krytyczne spostrzeżenie:' + konkretny praktyczny biznesowy wgląd z artykułu",
            
            "business_opportunities_en": "Specific business opportunities for European SMBs (300-500 chars)",
            "business_opportunities_uk": "Конкретні бізнес-можливості для європейських МСП (300-500 символів)",
            "business_opportunities_pl": "Konkretne możliwości biznesowe dla europejskich MŚP (300-500 znaków)",
            
            "lazysoft_recommendations_en": "RANDOM start: 'LAZYSOFT recommends:' OR 'Our team advises:' OR 'From LAZYSOFT experience:' OR 'Expert advice from LAZYSOFT:' OR 'Based on our expertise:' OR 'LAZYSOFT suggests:' + automation recommendations based on article insights (300-500 chars)",
            
            "lazysoft_recommendations_uk": "ВИПАДКОВИЙ початок: 'LAZYSOFT рекомендує:' АБО 'Наша команда радить:' АБО 'З досвіду LAZYSOFT:' АБО 'Експертна порада від LAZYSOFT:' АБО 'На основі нашої експертизи:' АБО 'LAZYSOFT пропонує:' АБО 'За нашими спостереженнями:' АБО 'Практична порада LAZYSOFT:' + рекомендації з автоматизації на основі інсайтів статті (300-500 символів)",
            
            "lazysoft_recommendations_pl": "LOSOWY początek: 'LAZYSOFT zaleca:' LUB 'Nasz zespół radzi:' LUB 'Z doświadczenia LAZYSOFT:' LUB 'Ekspercka rada od LAZYSOFT:' LUB 'Na podstawie naszej ekspertyzy:' + rekomendacje LAZYSOFT dotyczące automatyzacji (300-500 znaków)"
        }}

        CRITICAL: Use DIFFERENT random variations for EVERY article. Never repeat the same pattern twice.
        
        RANDOMIZATION RULES:
        - Each field must use a different variation from the previous article
        - Rotate through all available patterns systematically  
        - Ensure content diversity across all published articles
        - Mix formal and casual tones appropriately
        """

        try:
            self.logger.info("[AI] Генеруємо оригінальний 3-мовний контент ~2500 символів...")
            response = self._call_ai_model(main_prompt, max_tokens=5000)
            self.logger.info(f"[AI] Отримано відповідь: {len(response)} символів")
            
            cleaned = self._clean_json_response(response)
            self.logger.info(f"[AI] Очищено JSON: {len(cleaned)} символів")
            
            content_data = json.loads(cleaned)
            self.logger.info(f"[AI] Успішно розпарсено JSON з {len(content_data)} полями")
            
            # Перевіряємо чи заголовки унікальні та не ідентичні оригіналу
            original_clean = original_title.strip().lower() if original_title else ""
            
            # Перевіряємо чи AI згенерував ідентичні до оригіналу заголовки
            title_issues = []
            if content_data.get("title_en", "").strip().lower() == original_clean:
                title_issues.append("title_en identical to original")
            if content_data.get("title_uk", "").strip().lower() == original_clean:
                title_issues.append("title_uk identical to original") 
            if content_data.get("title_pl", "").strip().lower() == original_clean:
                title_issues.append("title_pl identical to original")
            
            # Перевіряємо чи всі заголовки ідентичні між собою
            if (content_data.get("title_en") == content_data.get("title_pl") or 
                content_data.get("title_en") == content_data.get("title_uk") or
                content_data.get("title_pl") == content_data.get("title_uk")):
                title_issues.append("titles identical between languages")
            
            if title_issues:
                self.logger.warning(f"[AI] Проблеми з заголовками: {', '.join(title_issues)}")
                self.logger.warning("[AI] Використовуємо fallback заголовки...")
                
                # Створюємо унікальні fallback заголовки замість оригінальних
                source_name = raw_article.source.name if raw_article.source else "Tech Source"
                topic = self._extract_main_topic(original_title)
                
                content_data["title_en"] = f"LAZYSOFT analyzes: {topic} insights from {source_name}"
                content_data["title_uk"] = f"LAZYSOFT аналізує: інсайти про {topic} від {source_name}"
                content_data["title_pl"] = f"LAZYSOFT analizuje: wglądy w {topic} od {source_name}"
            
        except Exception as e:
            self.logger.error(f"[AI] Помилка генерації контенту: {e}")
            self.logger.info("[AI] Використовуємо fallback контент")
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

            "business_insight_en": content_data.get("business_insight_en", ""),
            "business_insight_pl": content_data.get("business_insight_pl", ""),
            "business_insight_uk": content_data.get("business_insight_uk", ""),

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


    def _create_fallback_content_dict(self, raw_article: RawArticle, category_info: Dict) -> dict:
        """Створює fallback контент якщо AI недоступний"""
        original_title = raw_article.title or ""
        summary_src = raw_article.summary or raw_article.content or ""
        summary = summary_src[:500]
        
        # Створюємо унікальні fallback заголовки замість копіювання оригіналу
        source_name = raw_article.source.name if raw_article.source else "Tech Source"
        topic = self._extract_main_topic(original_title)

        return {
            "title_en": f"LAZYSOFT insights: {topic} analysis from {source_name}"[:300],
            "title_uk": f"LAZYSOFT інсайти: аналіз {topic} від {source_name}"[:300],
            "title_pl": f"LAZYSOFT spostrzeżenia: analiza {topic} od {source_name}"[:300],
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

            # Промпти з опису (обрізаємо для безпеки)
            "ai_image_prompt_en": f"LAZYSOFT insights: {topic} analysis from {source_name}"[:500],
            "ai_image_prompt_uk": f"LAZYSOFT інсайти: аналіз {topic} від {source_name}"[:500],
            "ai_image_prompt_pl": f"LAZYSOFT spostrzeżenia: analiza {topic} od {source_name}"[:500],
            

            # SEO – не пусті
            "meta_title_en": f"LAZYSOFT insights: {topic} analysis from {source_name}"[:500], 
            "meta_title_pl": f"LAZYSOFT spostrzeżenia: analiza {topic} od {source_name}"[:500], 
            "meta_title_uk": f"LAZYSOFT інсайти: аналіз {topic} від {source_name}"[:500],
            "meta_description_en": summary[:500], "meta_description_pl": summary[:500], "meta_description_uk": summary[:500],

            "category_slug": category_info["category"],
            "priority": category_info["priority"],
            "ai_model_used": "fallback",
            "cost": 0.0,
        }