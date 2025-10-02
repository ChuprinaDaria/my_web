import json
import logging
import re
from typing import Dict, Any, List, Optional

from .ai_processor_base import AINewsProcessor
from news.models import RawArticle


class AIContentProcessor(AINewsProcessor):
    """
    Модуль для створення тримовного контенту.
    З акцентом на надійний парсинг JSON-відповідей від моделі та розгорнуте логування.
    """

    # Мінімальний валідний JSON-скелет, щоб ніколи не повертати порожній об'єкт
    MINIMAL_JSON: Dict[str, Any] = {
        "title_en": "", "title_uk": "", "title_pl": "",
        "summary_en": "", "summary_uk": "", "summary_pl": "",
        "business_insight_en": "", "business_insight_uk": "", "business_insight_pl": "",
        "business_opportunities_en": "", "business_opportunities_uk": "", "business_opportunities_pl": "",
        "lazysoft_recommendations_en": "", "lazysoft_recommendations_uk": "", "lazysoft_recommendations_pl": "",
        "key_takeaways_en": [], "key_takeaways_uk": [], "key_takeaways_pl": [],
        "interesting_facts_en": [], "interesting_facts_uk": [], "interesting_facts_pl": [],
        "implementation_steps_en": [], "implementation_steps_uk": [], "implementation_steps_pl": []
    }

    CATEGORY_MAP: Dict[str, str] = {
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Окремий логер для цього класу
        self.logger = logging.getLogger(f"{__name__}.AIContentProcessor")

    # ---------------------------
    # УТИЛІТИ ДЛЯ ДОВЖИН/ТЕМ
    # ---------------------------

    def _clip_to_range(self, text: str, min_len: int = 2000, max_len: int = 3000) -> str:
        """Обрізає текст до діапазону символів із м'яким зрізом по крапці."""
        if not text:
            return ""
        t = text.strip()
        if len(t) > max_len:
            cut = t.rfind(". ", 0, max_len)
            if cut >= min_len:
                t = t[:cut + 1]
            else:
                t = t[:max_len]
        return t

    def _extract_main_topic(self, title: str) -> str:
        """Витягує основну тему з заголовка для fallback заголовків."""
        if not title:
            return "Technology"

        clean_title = title.strip()
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
        for keyword, topic in tech_keywords.items():
            if keyword in title_lower:
                return topic
        words = clean_title.split()[:3]
        return ' '.join(words) if words else "Technology"

    def _normalize_lengths(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Забезпечує довжину 2000–3000 символів для summary_*."""
        for lang in ("en", "uk", "pl"):
            key = f"summary_{lang}"
            content_data[key] = self._clip_to_range(content_data.get(key, ""), 2000, 3000)
        return content_data

    # ---------------------------
    # КАТЕГОРИЗАЦІЯ
    # ---------------------------

    def _categorize_article(self, raw_article: RawArticle) -> Dict[str, Any]:
        """AI категоризація статті."""
        categories = self.CATEGORY_MAP
        content_for_analysis = f"{(raw_article.title or '').strip()} {(raw_article.summary or '').strip()}".strip()

        prompt = f"""
Analyze this article and determine the most appropriate category.

Article: {content_for_analysis[:2000]}

Categories: {json.dumps(categories)}

Respond with just the category slug (e.g., "ai", "automation", etc.)
""".strip()

        try:
            category_slug = (self._call_ai_model(prompt, max_tokens=10) or "").strip().lower()
            if category_slug not in categories:
                category_slug = 'general'

            priority = 2
            lowered = content_for_analysis.lower()
            if any(w in lowered for w in ['breaking', 'urgent', 'major', 'launches']):
                priority = 3
            elif 'google' in lowered or 'microsoft' in lowered:
                priority = 3

            return {
                'category': category_slug,
                'priority': priority,
                'keywords': categories[category_slug].split(', ')
            }
        except Exception as e:
            self.logger.warning(f"⚠️ Помилка категоризації: {e}")
            return {'category': 'general', 'priority': 2, 'keywords': []}

    # ---------------------------
    # JSON ЧИСТКА/ПАРСИНГ
    # ---------------------------

    def _strip_markdown_fences(self, s: str) -> str:
        """Прибирає ```json / ``` обгортки, якщо вони є."""
        if not s:
            return ""
        s = s.strip()
        if s.startswith("```json"):
            s = s[7:]
        elif s.startswith("```"):
            s = s[3:]
        if s.endswith("```"):
            s = s[:-3]
        return s.strip()

    def _basic_repairs(self, s: str) -> str:
        """
        Прості ремонти JSON:
        - прибирання хвостових ком перед '}' або ']'
        - уніфікація нових рядків/пробілів
        """
        if not s:
            return s
        # прибрати коми перед закриваючими дужками
        s = re.sub(r",(\s*[}\]])", r"\1", s)
        # інколи моделі ставлять тильди/коментарі
        s = re.sub(r"\s*//.*?$", "", s, flags=re.MULTILINE)
        return s.strip()

    def _extract_top_level_json_object(self, text: str) -> Optional[str]:
        """
        Знаходить перший топ-рівневий JSON-об'єкт за балансом дужок,
        коректно обробляє лапки та escape.
        """
        if not text:
            return None

        start = text.find('{')
        if start == -1:
            self.logger.warning(f"[JSON] Не знайдено '{{' у відповіді. Прев'ю: {text[:200]!r}")
            return None

        brace_count = 0
        in_string = False
        escape_next = False
        end = None

        for i, ch in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if not in_string:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break

        if end is None:
            self.logger.warning("[JSON] Не вдалося знайти коректне закриття об'єкта. Можливо, відповідь обрізана.")
            # спроба: обрізати по останній "}"
            last_brace = text.rfind('}')
            if last_brace > start:
                return text[start:last_brace + 1]
            return None

        return text[start:end]

    def _safe_json_loads(self, s: str) -> Optional[Dict[str, Any]]:
        """Обгортає json.loads з логуванням останнього фрагмента помилки."""
        if not s:
            return None
        try:
            return json.loads(s)
        except json.JSONDecodeError as e:
            trail = s[max(0, e.pos - 120): e.pos + 120]
            self.logger.warning(f"[JSON] JSONDecodeError: {e}. Проблемний фрагмент +/-120 симв.: {trail!r}")
            return None
        except Exception as e:
            self.logger.exception(f"[JSON] Несподівана помилка json.loads: {e}")
            return None

    def _clean_json_response(self, response: str) -> str:
        """
        Очищає і витягує JSON з сирої відповіді моделі.
        Повертає мінімізований валідний JSON-рядок або MINIMAL_JSON (у рядку).
        """
        if not response or not response.strip():
            self.logger.warning("[JSON] Порожня відповідь від моделі.")
            return json.dumps(self.MINIMAL_JSON, ensure_ascii=False)

        raw_preview = response[:1000]
        self.logger.debug(f"[AI RAW 1k] {raw_preview!r}")

        s = self._strip_markdown_fences(response)
        s = self._basic_repairs(s)

        obj_text = self._extract_top_level_json_object(s)
        if not obj_text:
            self.logger.warning("[JSON] Не виділено топ-рівневий об'єкт. Повертаємо MINIMAL_JSON.")
            return json.dumps(self.MINIMAL_JSON, ensure_ascii=False)

        obj_text = self._basic_repairs(obj_text)

        # 1) Пряма спроба
        parsed = self._safe_json_loads(obj_text)
        if parsed is not None:
            self.logger.info(f"[JSON] Успішно розпарсено JSON з {len(parsed)} полями.")
            return json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))

        # 2) Спроба відрізати до останньої '}'
        last_brace = obj_text.rfind('}')
        if last_brace > 0:
            candidate = self._basic_repairs(obj_text[:last_brace + 1])
            parsed = self._safe_json_loads(candidate)
            if parsed is not None:
                self.logger.info(f"[JSON] Відновлено JSON обрізанням. Полів: {len(parsed)}.")
                return json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))

        # 3) Спроба знайти мінімальне поле title_en і зібрати скелет
        m = re.search(r'"title_en"\s*:\s*"([^"]*)"', obj_text)
        if m:
            title_en = m.group(1)
            minimal = dict(self.MINIMAL_JSON)
            minimal["title_en"] = title_en
            minimal["title_uk"] = title_en
            minimal["title_pl"] = title_en
            self.logger.info("[JSON] Сконструйовано мінімальний JSON на основі title_en.")
            return json.dumps(minimal, ensure_ascii=False, separators=(',', ':'))

        self.logger.warning("[JSON] Усі спроби відновити JSON провалились. Повертаємо MINIMAL_JSON.")
        return json.dumps(self.MINIMAL_JSON, ensure_ascii=False)

    # ---------------------------
    # ОСНОВНА ГЕНЕРАЦІЯ
    # ---------------------------

    def _ensure_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Гарантує наявність усіх ключів із MINIMAL_JSON."""
        for k, v in self.MINIMAL_JSON.items():
            if k not in data:
                data[k] = v
        return data

    def _create_multilingual_content(
        self,
        raw_article: RawArticle,
        category_info: Dict[str, Any],
        full_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Створює тримовний ОРИГІНАЛЬНИЙ бізнес-аналіз з RSS (~2000–3000 символів)."""

        original_title = raw_article.title or ""
        content_to_use = full_content or raw_article.content or raw_article.summary or ""
        max_ai_content = min(len(content_to_use), 8000)
        content_for_ai = content_to_use[:max_ai_content]
        category = category_info.get("category", "general")

        self.logger.info(
            f"[AI INPUT] Стаття: {original_title[:60]}... | Source: "
            f"{raw_article.source.name if raw_article.source else 'Unknown'} | "
            f"Full: {len(content_to_use)} | ToAI: {len(content_for_ai)} | Category: {category}"
        )

        source_name = raw_article.source.name if raw_article.source else "Unknown Source"
        original_url = raw_article.original_url or ""

        main_prompt = f"""
OUTPUT STRICTLY VALID, MINIFIED JSON. NO MARKDOWN. NO EXTRA TEXT. NO COMMENTS.

You are LAZYSOFT's senior tech analyst. Your job is to ANALYZE and SYNTHESIZE information from tech articles for European SMB audience, NOT to translate or copy.

CRITICAL ANTI-PLAGIARISM RULES:
- NEVER copy sentences from the original article
- NEVER translate article text directly
- ALWAYS write in your own words and add SMB context

ORIGINAL ARTICLE INFO:
Title: {original_title}
Source: {source_name}
Content to analyze: {content_for_ai}
Category: {category}

CONTENT REQUIREMENTS (2000-3000 chars per language, en/uk/pl):
- What happened (your words)
- Key technologies/companies/numbers
- Why it matters for European SMBs
- Practical implications
- LAZYSOFT perspective on automation

Return JSON with keys:
{json.dumps(self.MINIMAL_JSON, ensure_ascii=False)}
But fill them with real content (not empty), including titles and arrays.
""".strip()

        try:
            # Якщо підтримується – просимо саме JSON-об'єкт
            response = self._call_ai_model(
                main_prompt,
                max_tokens=5000,
                response_format={"type": "json_object"}
            )
            self.logger.info(f"[AI] Отримано відповідь, довжина: {len(response) if response else 0}")
            self.logger.debug(f"[AI RAW 1k AFTER] {(response or '')[:1000]!r}")

            cleaned = self._clean_json_response(response or "")
            self.logger.info(f"[AI] Після чистки JSON довжина: {len(cleaned)}")

            if cleaned.strip() in ("", "{}", "[]"):
                self.logger.warning("[AI] Порожній або мінімальний JSON — викликаємо fallback.")
                return self._create_fallback_content_dict(raw_article, category_info, content_to_use)

            content_data = self._safe_json_loads(cleaned)
            if content_data is None or not isinstance(content_data, dict) or not content_data:
                self.logger.warning("[AI] Не вдалося завантажити JSON після чистки — fallback.")
                return self._create_fallback_content_dict(raw_article, category_info, content_to_use)

            content_data = self._ensure_keys(content_data)

            # Перевірка заголовків
            original_clean = original_title.strip().lower()
            title_issues: List[str] = []

            te = (content_data.get("title_en") or "").strip()
            tu = (content_data.get("title_uk") or "").strip()
            tp = (content_data.get("title_pl") or "").strip()

            if te.lower() == original_clean:
                title_issues.append("title_en identical to original")
            if tu.lower() == original_clean:
                title_issues.append("title_uk identical to original")
            if tp.lower() == original_clean:
                title_issues.append("title_pl identical to original")

            if te and (te == tu or te == tp) or (tu and tu == tp):
                title_issues.append("titles identical between languages")

            if title_issues:
                self.logger.warning(f"[AI] Проблеми з заголовками: {', '.join(title_issues)} — застосовуємо fallback заголовки.")
                topic = self._extract_main_topic(original_title)
                src = raw_article.source.name if raw_article.source else "Tech Source"
                content_data["title_en"] = f"LAZYSOFT analyzes: {topic} insights from {src}"
                content_data["title_uk"] = f"LAZYSOFT аналізує: інсайти про {topic} від {src}"
                content_data["title_pl"] = f"LAZYSOFT analizuje: wglądy w {topic} od {src}"

        except json.JSONDecodeError as e:
            self.logger.error(
                f"❌ [AI JSON PARSE] Стаття: {original_title[:60]}... | Помилка: {e}"
            )
            return self._create_fallback_content_dict(raw_article, category_info, content_to_use)

        except Exception as e:
            self.logger.exception(
                f"❌ [AI CRITICAL] Стаття: {original_title[:60]}... | Тип: {type(e).__name__} | Деталі: {e}"
            )
            return self._create_fallback_content_dict(raw_article, category_info, content_to_use)

        # Нормалізація довжин summary
        content_data = self._normalize_lengths(content_data)

        # SEO / CTA / cost
        seo = self._generate_seo_metadata(content_data, category)
        cta_buttons = self._generate_cta_buttons(category)
        cost = self._calculate_cost(main_prompt, json.dumps(content_data, ensure_ascii=False))

        title_en = content_data.get("title_en", original_title)

        return {
            "title_en": title_en,
            "title_pl": content_data.get("title_pl", original_title),
            "title_uk": content_data.get("title_uk", original_title),
            "summary_en": content_data.get("summary_en", (content_for_ai or "")[:2500]),
            "summary_pl": content_data.get("summary_pl", (content_for_ai or "")[:2500]),
            "summary_uk": content_data.get("summary_uk", (content_for_ai or "")[:2500]),
            "business_insight_en": content_data.get("business_insight_en", ""),
            "business_insight_pl": content_data.get("business_insight_pl", ""),
            "business_insight_uk": content_data.get("business_insight_uk", ""),
            "business_opportunities_en": content_data.get("business_opportunities_en", ""),
            "business_opportunities_pl": content_data.get("business_opportunities_pl", ""),
            "business_opportunities_uk": content_data.get("business_opportunities_uk", ""),
            "lazysoft_recommendations_en": content_data.get("lazysoft_recommendations_en", ""),
            "lazysoft_recommendations_pl": content_data.get("lazysoft_recommendations_pl", ""),
            "lazysoft_recommendations_uk": content_data.get("lazysoft_recommendations_uk", ""),
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

    # ---------------------------
    # FALLBACK
    # ---------------------------

    def _create_fallback_content_dict(
        self,
        raw_article: RawArticle,
        category_info: Dict[str, Any],
        content_to_use: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback контент - АНАЛІТИЧНИЙ, не копіює оригінал."""
        original_title = raw_article.title or "Tech Update"
        source_name = raw_article.source.name if raw_article.source else "tech source"
        category = category_info.get('category', 'technology')

        full_content = content_to_use or raw_article.content or raw_article.summary or ""
        self.logger.warning(
            "⚠️ [FALLBACK] AI недоступний або віддав поганий JSON.\n"
            f"   Стаття: '{original_title[:80]}...'\n"
            f"   Категорія: {category}\n"
            f"   Source: {source_name}\n"
            f"   Content length: {len(full_content)}"
        )

        analytical_title_en = f"Latest {category} developments: {source_name} reports on {original_title[:50]}"
        analytical_title_uk = f"Останні новини {category}: {source_name} повідомляє про {original_title[:50]}"
        analytical_title_pl = f"Najnowsze wiadomości {category}: {source_name} informuje o {original_title[:50]}"

        summary_intro_en = f"According to {source_name}, recent developments in {category} sector indicate "
        summary_intro_uk = f"За даними {source_name}, останні розробки в секторі {category} вказують на "
        summary_intro_pl = f"Według {source_name}, najnowsze rozwój w sektorze {category} wskazuje na "
        content_snippet = full_content[:1500] if full_content else "technological advancement in the industry"

        title_words = [w for w in (original_title or "").split() if len(w) > 4]

        return {
            "title_en": analytical_title_en,
            "title_pl": analytical_title_pl,
            "title_uk": analytical_title_uk,

            "summary_en": f"{summary_intro_en}significant changes in business technology landscape. "
                          f"{content_snippet} For European SMBs, these developments may present opportunities "
                          f"for process automation and efficiency improvements. Detailed AI analysis temporarily unavailable.",

            "summary_pl": f"{summary_intro_pl}istotne zmiany w krajobrazie technologii biznesowej. "
                          f"{content_snippet} Dla europejskich MŚP rozwój ten może stanowić okazję do automatyzacji "
                          f"procesów i poprawy efektywności. Szczegółowa analiza AI tymczasowo niedostępna.",

            "summary_uk": f"{summary_intro_uk}значні зміни в ландшафті бізнес-технологій. "
                          f"{content_snippet} Для європейських МСП ці розробки можуть представляти можливості "
                          f"для автоматизації процесів та підвищення ефективності. Детальний AI аналіз тимчасово недоступний.",

            "business_insight_en": f"Based on {source_name} report about {category}, European SMBs should "
                                   f"monitor these developments for potential automation opportunities.",
            "business_insight_pl": f"Na podstawie raportu {source_name} dotyczącego {category}, europejskie MŚP "
                                   f"powinny monitorować ten rozwój pod kątem automatyzacji.",
            "business_insight_uk": f"На основі звіту {source_name} про {category}, європейські МСП мають "
                                   f"відстежувати ці розробки щодо можливостей автоматизації.",

            "business_opportunities_en": f"Technology developments reported by {source_name} may offer "
                                         f"process automation potential. LAZYSOFT recommends assessment.",
            "business_opportunities_pl": f"Rozwój technologiczny zgłoszony przez {source_name} może oferować "
                                         f"potencjał automatyzacji procesów. Zalecamy analizę.",
            "business_opportunities_uk": f"Розробки від {source_name} можуть запропонувати потенціал "
                                         f"автоматизації. Рекомендуємо оцінку.",

            "lazysoft_recommendations_en": f"Contact LAZYSOFT for professional analysis of how {category} "
                                           f"developments from {source_name} can be applied to your automation strategy.",
            "lazysoft_recommendations_pl": f"Skontaktuj się z LAZYSOFT, aby ocenić zastosowanie rozwoju {category} "
                                           f"od {source_name} w Twojej strategii automatyzacji.",
            "lazysoft_recommendations_uk": f"Зв'яжіться з LAZYSOFT для аналізу застосування розробок {category} "
                                           f"від {source_name} у вашій стратегії автоматизації.",

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
            "interesting_facts_en": [
                f"Technology development reported by {source_name}",
                f"Potential impact on {category} sector",
                "Automation opportunities identified"
            ],
            "interesting_facts_pl": [
                f"Rozwój technologiczny zgłoszony przez {source_name}",
                f"Potencjalny wpływ na sektor {category}",
                "Zidentyfikowane możliwości automatyzacji"
            ],
            "interesting_facts_uk": [
                f"Технологічний розвиток від {source_name}",
                f"Потенційний вплив на сектор {category}",
                "Виявлені можливості автоматизації"
            ],
            "implementation_steps_en": [
                "Assess current business processes",
                "Identify automation opportunities",
                "Plan technology integration",
                "Execute and monitor results"
            ],
            "implementation_steps_pl": [
                "Oceń obecne procesy biznesowe",
                "Zidentyfikuj możliwości automatyzacji",
                "Zaplanuj integrację technologii",
                "Wykonaj i monitoruj wyniki"
            ],
            "implementation_steps_uk": [
                "Оцініть поточні бізнес-процеси",
                "Визначте можливості автоматизації",
                "Сплануйте інтеграцію технологій",
                "Виконайте та відстежуйте результати"
            ],
        }

    # ---------------------------
    # ПУБЛІЧНИЙ МЕТОД
    # ---------------------------

    def generate_full_content(self, content: str, language: str) -> str:
        """Генерує повний Business Impact контент (2000-3000 символів) певною мовою."""
        try:
            prompt = f"""
OUTPUT STRICTLY VALID PLAIN TEXT (NO MARKDOWN).
Як експерт LAZYSOFT з автоматизації бізнес-процесів, створи детальний Business Impact аналіз на {language} мові
на основі наступної статті (2000-3000 символів, практичний фокус, адаптовано для {language} ринку):

{content}

Структура:
1) Тренди та вплив
2) Можливості для підприємців
3) Практичні кроки
4) Ризики та мінімізація
5) Конкурентні переваги
""".strip()

            full_content = self._call_ai_model(prompt, max_tokens=3000)
            self.logger.info(f"[BI] Згенеровано Business Impact ({language}) довжиною: {len(full_content) if full_content else 0}")
            return (full_content or "").strip()
        except Exception as e:
            self.logger.warning(f"⚠️ Помилка генерації Business Impact для {language}: {e}")
            return content or ""
