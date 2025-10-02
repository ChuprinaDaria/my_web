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

    def _create_multilingual_content(self, raw_article: RawArticle, category_info: Dict, full_content: str = None) -> dict:
        """Створює тримовний ОРИГІНАЛЬНИЙ бізнес-аналіз з RSS (~1000–1200 символів)."""
        original_title = raw_article.title or ""
        # Використовуємо переданий full_content або контент з raw_article
        if full_content:
            content_to_use = full_content
        else:
            content_to_use = raw_article.content or raw_article.summary or ""
        
        # Динамічний ліміт: до 8К символів (безпечно для Claude API + промпт)
        max_ai_content = min(len(content_to_use), 8000)
        content_for_ai = content_to_use[:max_ai_content]
        
        self.logger.info(
            f"[AI INPUT] Стаття: {raw_article.title[:60]}...\n"
            f"   Full content: {len(content_to_use)} символів\n"
            f"   Передаємо AI: {len(content_for_ai)} символів\n"
            f"   Source: {raw_article.source.name if raw_article.source else 'Unknown'}"
        )
        category = category_info["category"]

        # Підготовуємо дані для промпту
        source_name = raw_article.source.name if raw_article.source else "Unknown Source"
        original_url = raw_article.original_url or ""
        
        main_prompt = f"""
You are LAZYSOFT's senior tech analyst. Your job is to ANALYZE and SYNTHESIZE information from tech articles for European SMB audience, NOT to translate or copy.

CRITICAL ANTI-PLAGIARISM RULES:
🚫 NEVER copy sentences from the original article
🚫 NEVER translate article text directly
🚫 NEVER use exact phrases even in quotes
✅ ALWAYS analyze, interpret, and explain in YOUR OWN WORDS
✅ ALWAYS add business context and SMB perspective
✅ ALWAYS synthesize information into original analysis

ORIGINAL ARTICLE INFO:
Title: {original_title}
Source: {source_name}
Content to analyze: {content_for_ai}
Category: {category}

YOUR TASK:
1. READ and UNDERSTAND the article
2. EXTRACT key facts, technologies, companies mentioned
3. ANALYZE what this means for European SMBs
4. WRITE ORIGINAL analysis in your own words
5. CREATE unique business-focused titles that describe the news

TITLE REQUIREMENTS:
- Must be ORIGINAL, not copy of source title
- Format examples:
  * "Новини про [technology/company]: що каже [Source Name] про [key point]"
  * "Останні розробки [topic]: аналіз від [Source Name]"  
  * "[Source Name] повідомляє про [main point] - що це означає для бізнесу"
- Include source name for credibility
- Describe WHAT the article discusses, not copy its title

CONTENT REQUIREMENTS (2000-3000 chars per language):
- Write as LAZYSOFT analyst, not as article translator
- Structure: 
  1. What happened (in your words)
  2. Key technologies/companies/numbers involved
  3. Why it matters for European SMBs
  4. Practical implications
- Use phrases like:
  * "За даними [Source], ..."
  * "[Source Name] повідомляє, що..."
  * "Згідно з аналізом від [Source], ..."
  * "Дослідження показує..."
- Include specific facts but REPHRASE them
- Add LAZYSOFT perspective on automation opportunities

EXAMPLE OF ORIGINAL ANALYSIS:

Article: "Google AI Max Early Case Studies: Performance Analysis and Script"
Source: Search Engine Land

❌ BAD (copying):
"Google's AI Max combines Dynamic Search Ads and Performance Max. The script creates two tabs in your Sheet: AI Max Performance Max search term data with headlines, landing pages, and performance metrics..."

✅ GOOD (original analysis):
"Search Engine Land опублікував дослідження ефективності Google AI Max, що об'єднує технології Dynamic Search Ads та Performance Max. Аналіз трьох секторів виявив цікаві патерни: туристичний сектор показав 22.5% перетину з існуючими запитами, що може свідчити про перерозподіл трафіку, тоді як індустрія моди виявила 81.3% абсолютно нових запитів - це справжня можливість для зростання. Для МСП особливо цінним є автоматизований скрипт для Google Sheets, який дозволяє швидко аналізувати ефективність кампаній без ручної роботи..."

VERIFICATION BEFORE RESPONDING:
☑ Did I write in MY OWN WORDS?
☑ Did I add business context original article doesn't have?
☑ Would this pass plagiarism check?
☑ Did I mention source but not copy their text?
☑ Are titles ORIGINAL, not translated?
☑ Did I include specific facts/numbers but rephrase them?

KEY TAKEAWAYS (3-5 bullet points per language):
- Extract SPECIFIC facts, numbers, technologies mentioned IN THIS ARTICLE
- NOT generic automation advice - only what THIS article discusses
- Example: "Google AI Max shows 81% new query discovery" (specific!)
- NOT: "AI can help businesses" (too generic!)

INTERESTING FACTS (2-3 per language):
- Statistics or data points FROM THE ARTICLE with source mention
- Industry trends DISCUSSED IN THE ARTICLE
- Company announcements or tech developments FROM ARTICLE CONTENT

IMPLEMENTATION STEPS (3-4 per language):
- Practical steps based on WHAT THE ARTICLE DISCUSSES
- If article about AI tool - steps to implement THAT tool
- If article about trend - steps to adapt to THAT trend
- Keep steps actionable and specific to article topic

OUTPUT JSON ONLY:
        {{
            "title_en": "Original analytical title mentioning source and key point",
            "title_uk": "Оригінальний аналітичний заголовок з джерелом",
            "title_pl": "Oryginalny tytuł analityczny ze źródłem",
            
            "summary_en": "ORIGINAL analysis in your own words (2000-3000 chars) - NOT translation",
            "summary_uk": "ОРИГІНАЛЬНИЙ аналіз своїми словами (2000-3000 символів) - НЕ переклад",
            "summary_pl": "ORYGINALNA analiza własnymi słowami (2000-3000 znaków) - NIE tłumaczenie",
            
            "business_insight_en": "Unique business insight analyzing article findings for SMBs",
            "business_insight_uk": "Унікальний бізнес-інсайт з аналізом для МСП",
            "business_insight_pl": "Unikalny wgląd biznesowy z analizą dla MŚP",
            
            "business_opportunities_en": "LAZYSOFT perspective on automation opportunities (300-500 chars)",
            "business_opportunities_uk": "Перспектива LAZYSOFT щодо можливостей автоматизації (300-500 символів)",
            "business_opportunities_pl": "Perspektywa LAZYSOFT dotycząca możliwości automatyzacji (300-500 znaków)",
            
            "lazysoft_recommendations_en": "LAZYSOFT automation recommendations (300-500 chars)",
            "lazysoft_recommendations_uk": "Рекомендації LAZYSOFT з автоматизації (300-500 символів)",
            "lazysoft_recommendations_pl": "Rekomendacje LAZYSOFT dotyczące automatyzacji (300-500 znaków)",
            
            "key_takeaways_en": ["specific fact from article", "specific tech mentioned", "specific number"],
            "key_takeaways_uk": ["конкретний факт зі статті", "конкретна технологія", "конкретна цифра"],
            "key_takeaways_pl": ["konkretny fakt z artykułu", "konkretna technologia", "konkretna liczba"],
            
            "interesting_facts_en": ["stat FROM article with source", "trend FROM article"],
            "interesting_facts_uk": ["статистика ЗІ статті з джерелом", "тренд ЗІ статті"],
            "interesting_facts_pl": ["statystyka Z artykułu ze źródłem", "trend Z artykułu"],
            
            "implementation_steps_en": ["step 1 based on article topic", "step 2", "step 3"],
            "implementation_steps_uk": ["крок 1 на основі теми статті", "крок 2", "крок 3"],
            "implementation_steps_pl": ["krok 1 oparty na temacie artykułu", "krok 2", "krok 3"]
        }}
        """

        try:
            self.logger.info("[AI] Генеруємо оригінальний 3-мовний контент ~2000 символів...")
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
            
        except json.JSONDecodeError as e:
            self.logger.error(
                f"❌ [AI JSON PARSE] Стаття: {raw_article.title[:60]}...\n"
                f"   Помилка: {e}\n"
                f"   AI Response (перші 500 chars): {response[:500] if 'response' in locals() else 'N/A'}\n"
                f"   Після очищення: {cleaned[:500] if 'cleaned' in locals() else 'N/A'}\n"
                f"   Content length: {len(content_for_ai)}"
            )
            content_data = self._create_fallback_content_dict(raw_article, category_info, content_to_use)
            
        except Exception as e:
            self.logger.error(
                f"❌ [AI CRITICAL] Стаття: {raw_article.title[:60]}...\n"
                f"   Тип: {type(e).__name__}\n"
                f"   Деталі: {e}\n"
                f"   Content передано: {len(content_for_ai) if 'content_for_ai' in locals() else 'N/A'} символів"
            )
            content_data = self._create_fallback_content_dict(raw_article, category_info, content_to_use)

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

            # Нові поля для детального аналізу
            "key_takeaways_en": content_data.get("key_takeaways_en", []),
            "key_takeaways_pl": content_data.get("key_takeaways_pl", []),
            "key_takeaways_uk": content_data.get("key_takeaways_uk", []),
            "interesting_facts_en": content_data.get("interesting_facts_en", []),
            "interesting_facts_pl": content_data.get("interesting_facts_pl", []),
            "interesting_facts_uk": content_data.get("interesting_facts_uk", []),

            "implementation_steps_en": content_data.get("implementation_steps_en", []),
            "implementation_steps_pl": content_data.get("implementation_steps_pl", []),
            "implementation_steps_uk": content_data.get("implementation_steps_uk", []),

            "category_slug": category,
            "priority": category_info.get("priority", 2),

            "ai_model_used": self.preferred_model,
            "processing_time": 0,
            "cost": cost,
            **seo,
            "cta_buttons": cta_buttons
        }


    def _create_fallback_content_dict(self, raw_article: RawArticle, category_info: Dict, content_to_use: str = None) -> dict:
        """Fallback контент - АНАЛІТИЧНИЙ, не копіює оригінал"""
        
        # ВАЖЛИВО: логуємо що fallback спрацював
        self.logger.warning(
            f"⚠️ [FALLBACK] AI недоступний! Стаття: '{raw_article.title[:80]}...'\n"
            f"   Категорія: {category_info.get('category', 'unknown')}\n"
            f"   Source: {raw_article.source.name if raw_article.source else 'N/A'}\n"
            f"   Content length: {len(content_to_use or raw_article.content or '')} символів\n"
            f"   ⚠️ Використовуємо fallback - контент буде базовим!"
        )
        
        original_title = raw_article.title or "Tech Update"
        source_name = raw_article.source.name if raw_article.source else "tech source"
        category = category_info.get('category', 'technology')
        
        # Беремо контент для базового аналізу
        if content_to_use:
            full_content = content_to_use
        else:
            full_content = raw_article.content or raw_article.summary or ""
        
        # Створюємо АНАЛІТИЧНИЙ заголовок, НЕ копію оригіналу
        analytical_title_en = f"Latest {category} developments: {source_name} reports on {original_title[:50]}"
        analytical_title_uk = f"Останні новини {category}: {source_name} повідомляє про {original_title[:50]}"
        analytical_title_pl = f"Najnowsze wiadomości {category}: {source_name} informuje o {original_title[:50]}"
        
        # Fallback summary - базовий аналіз
        summary_intro_en = f"According to {source_name}, recent developments in {category} sector indicate "
        summary_intro_uk = f"За даними {source_name}, останні розробки в секторі {category} вказують на "
        summary_intro_pl = f"Według {source_name}, najnowsze rozwój w sektorze {category} wskazuje na "
        
        # Додаємо частину оригінального контенту як context, але з введенням
        content_snippet = full_content[:1500] if full_content else "technological advancement in the industry"
        
        # Витягуємо ключові слова зі статті для key_takeaways
        title_words = [w for w in original_title.split() if len(w) > 4]
        
        return {
            # АНАЛІТИЧНІ заголовки з джерелом
            "title_en": analytical_title_en, 
            "title_pl": analytical_title_pl, 
            "title_uk": analytical_title_uk,
            
            # Базовий аналіз з введенням джерела
            "summary_en": f"{summary_intro_en}significant changes in business technology landscape. {content_snippet} For European SMBs, these developments may present opportunities for process automation and efficiency improvements. Detailed AI analysis temporarily unavailable - refer to original source for complete information.",
            
            "summary_pl": f"{summary_intro_pl}istotne zmiany w krajobrazie technologii biznesowej. {content_snippet} Dla europejskich MŚP rozwój ten może stanowić okazję do automatyzacji procesów i poprawy efektywności. Szczegółowa analiza AI tymczasowo niedostępna.",
            
            "summary_uk": f"{summary_intro_uk}значні зміни в ландшафті бізнес-технологій. {content_snippet} Для європейських МСП ці розробки можуть представляти можливості для автоматизації процесів та підвищення ефективності. Детальний AI аналіз тимчасово недоступний.",

            # Insights з аналітичним контекстом
            "business_insight_en": f"Based on {source_name} report about {category}, European SMBs should monitor these technological developments for potential automation and optimization opportunities. Full analysis requires detailed review.",
            
            "business_insight_pl": f"Na podstawie raportu {source_name} dotyczącego {category}, europejskie MŚP powinny monitorować te rozwój technologiczne pod kątem potencjalnych możliwości automatyzacji. Pełna analiza wymaga szczegółowego przeglądu.",
            
            "business_insight_uk": f"На основі звіту {source_name} про {category}, європейські МСП мають відстежувати ці технологічні розробки для потенційних можливостей автоматизації. Повний аналіз потребує детального огляду.",
            
            # Opportunities - не generic!
            "business_opportunities_en": f"Technology developments reported by {source_name} may offer process automation potential. LAZYSOFT recommends detailed assessment for specific business applications.",
            
            "business_opportunities_pl": f"Rozwój technologiczny zgłoszony przez {source_name} może oferować potencjał automatyzacji procesów. LAZYSOFT zaleca szczegółową ocenę dla konkretnych zastosowań biznesowych.",
            
            "business_opportunities_uk": f"Технологічні розробки від {source_name} можуть запропонувати потенціал автоматизації. LAZYSOFT рекомендує детальну оцінку для конкретних бізнес-застосувань.",
            
            # LAZYSOFT recommendations
            "lazysoft_recommendations_en": f"Contact LAZYSOFT for professional analysis of how {category} developments from {source_name} can be applied to your business automation strategy.",
            
            "lazysoft_recommendations_pl": f"Skontaktuj się z LAZYSOFT w celu profesjonalnej analizy, jak rozwój {category} od {source_name} może być zastosowany do Twojej strategii automatyzacji biznesowej.",
            
            "lazysoft_recommendations_uk": f"Зв'яжіться з LAZYSOFT для професійного аналізу того, як розробки {category} від {source_name} можуть бути застосовані до вашої стратегії автоматизації бізнесу.",
            
            # Нові поля для детального аналізу
            "key_takeaways_en": [
                f"Article discusses {title_words[0] if title_words else 'technology'}",
                f"Source: {source_name}",
                f"Category: {category}"
            ],
            "key_takeaways_uk": [
                f"Стаття обговорює {title_words[0] if title_words else 'технологію'}",
                f"Джерело: {source_name}",
                f"Категорія: {category}"
            ],
            "key_takeaways_pl": [
                f"Artykuł omawia {title_words[0] if title_words else 'technologię'}",
                f"Źródło: {source_name}",
                f"Kategoria: {category}"
            ],
            "interesting_facts_en": [f"Technology development reported by {source_name}", f"Potential impact on {category} sector", "Automation opportunities identified"],
            "interesting_facts_pl": [f"Rozwój technologiczny zgłoszony przez {source_name}", f"Potencjalny wpływ na sektor {category}", "Zidentyfikowane możliwości automatyzacji"],
            "interesting_facts_uk": [f"Технологічний розвиток від {source_name}", f"Потенційний вплив на сектор {category}", "Виявлені можливості автоматизації"],
            
            "implementation_steps_en": ["Assess current business processes", "Identify automation opportunities", "Plan technology integration", "Execute and monitor results"],
            "implementation_steps_pl": ["Oceń obecne procesy biznesowe", "Zidentyfikuj możliwości automatyzacji", "Zaplanuj integrację technologii", "Wykonaj i monitoruj wyniki"],
            "implementation_steps_uk": ["Оцініть поточні бізнес-процеси", "Визначте можливості автоматизації", "Сплануйте інтеграцію технологій", "Виконайте та відстежуйте результати"],
        }

    def generate_full_content(self, content: str, language: str) -> str:
        """Генерує повний Business Impact контент на конкретній мові (2000-3000 символів)"""
        try:
            # Використовуємо AI для генерації детального Business Impact контенту
            prompt = f"""
Як експерт LAZYSOFT з автоматизації бізнес-процесів, створи детальний Business Impact аналіз на {language} мові на основі наступної статті:

{content}

Структура аналізу:
1. Ключові технологічні тренди та їх вплив на бізнес
2. Конкретні можливості для автоматизації та оптимізації
3. Практичні кроки впровадження для МСБ
4. ROI оцінка та потенційні економії
5. Ризики та способи їх мінімізації
6. Конкурентні переваги та можливості росту

Вимоги:
- Довжина: 2000-3000 символів
- Практичний фокус на автоматизації
- Конкретні цифри та приклади
- Адаптовано для {language} ринку
- Стиль LAZYSOFT: експертний, але зрозумілий
- НЕ копіюй оригінальний текст - створюй ОРИГІНАЛЬНИЙ аналіз
"""
            
            full_content = self._call_ai_model(prompt, max_tokens=3000)
            return full_content.strip()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Помилка генерації Business Impact для {language}: {e}")
            # Повертаємо оригінальний контент якщо генерація не вдалася
            return content