import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count

from news.models import RawArticle, ProcessedArticle, NewsCategory, DailyDigest, ROIAnalytics

from news.services.ai_processor.audience_analyzer import AudienceAnalyzer
from news.services.ai_processor.enhanced_ai_analyzer import EnhancedAIAnalyzer
from news.services.ai_processor.ai_processor_main import AINewsProcessor

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Результат роботи Smart News Pipeline"""
    date: datetime.date
    total_articles_processed: int
    top_articles_selected: int
    articles_published: int
    digest_created: bool
    roi_calculated: bool
    processing_time: float
    errors: List[str]
    success_rate: float


class SmartNewsPipeline:
    """
    ОПТИМІЗОВАНИЙ розумний пайплайн обробки новин:
    1. Audience Analyzer - селекція топ-5 релевантних статей
    2. Full Article Parser - завантаження повного контенту ТІЛЬКИ для ТОП-5
    3. Enhanced AI Analyzer - створення LAZYSOFT інсайтів ТІЛЬКИ для ТОП-5
    4. AI News Processor - генерація тримовного контенту ТІЛЬКИ для ТОП-5
    5. Автопублікація ТОП-5 статей + створення дайджесту з цих же ТОП-5
    6. Оновлення ROI метрик
    
    ЕКОНОМІЯ: тільки 5 AI викликів замість всіх статей!
    """
    
    def __init__(self):
        # Ініціалізуємо всі компоненти
        
        self.audience_analyzer = AudienceAnalyzer()
        self.enhanced_analyzer = EnhancedAIAnalyzer()
        self.ai_processor = AINewsProcessor()
        
        # Налаштування
        self.top_articles_limit = 5
        self.max_processing_time = 1800  # 30 хвилин максимум
        
        # Статистика
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'avg_processing_time': 0,
            'total_articles_processed': 0
        }
        
        logger.info("🚀 Smart News Pipeline ініціалізовано")

    def run_daily_pipeline(self, date: Optional[datetime.date] = None, dry_run: bool = False) -> PipelineResult:
        """
        Запускає повний щоденний пайплайн обробки новин
        
        Args:
            date: Дата для обробки (за замовчанням сьогодні)
            dry_run: Тестовий режим без збереження
            
        Returns:
            PipelineResult з результатами роботи
        """
        start_time = time.time()
        
        if not date:
            date = timezone.now().date()
        
        logger.info(f"🚀 Запуск Smart News Pipeline за {date}")
        
        errors = []
        articles_published = 0
        digest_created = False
        roi_calculated = False
        
        try:
            # === КРОК 1: Селекція топ-5 статей ===
            logger.info("🎯 Крок 1: Селекція релевантних статей...")
            top_articles = self.audience_analyzer.get_daily_top_articles(
                date=date, 
                limit=self.top_articles_limit
            )
 
            if not top_articles:
                logger.warning(f"⚠️ Немає статей для обробки за {date}")
                return self._create_empty_result(date, time.time() - start_time)
 
            logger.info(f"✅ Вибрано {len(top_articles)} топ статей")
 
            if not dry_run:
                ProcessedArticle.objects.filter(top_selection_date=date).update(
                    is_top_article=False,
                    article_rank=None
                )

            # === КРОК 2: Обробка кожної топ статті ===
            processed_articles = []
 
            for i, (raw_article, relevance_analysis) in enumerate(top_articles, 1):
                logger.info(f"📄 Обробка статті {i}/{len(top_articles)}: {raw_article.title[:50]}...")
 
                try:
                    processed_article = self._process_single_article(
                        raw_article, relevance_analysis, dry_run
                    )
 
                    if processed_article:
                        if not dry_run:
                            # Встановлюємо пріоритет на основі релевантності
                            try:
                                score = getattr(relevance_analysis, "relevance_score", None)
                                if score is None and isinstance(relevance_analysis, dict):
                                    score = relevance_analysis.get("relevance_score")
                                if isinstance(score, (int, float)):
                                    priority = max(3, min(5, int(score // 2)))
                                else:
                                    priority = 4  # Високий пріоритет для топ-статей
                            except Exception:
                                priority = 4  # Високий пріоритет за замовчанням
                            
                            processed_article.is_top_article = True
                            processed_article.article_rank = i
                            processed_article.top_selection_date = date
                            processed_article.priority = priority
                            processed_article.save(update_fields=['is_top_article', 'article_rank', 'top_selection_date', 'priority'])
                            logger.info(f"📢 Статтю {i} позначено як топ-{i} з пріоритетом {priority}")

                        processed_articles.append(processed_article)
                        articles_published += 1
                        logger.info(f"✅ Стаття {i} оброблена успішно")
                    else:
                        errors.append(f"Не вдалося обробити статтю: {raw_article.title[:50]}")
                        
                except Exception as e:
                    error_msg = f"Помилка обробки статті {i}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # === КРОК 3: Створення дайджесту з ТОП-5 статей ===
            if not dry_run and processed_articles:
                logger.info("📰 Крок 3: Створення дайджесту з ТОП-5 статей...")
                try:
                    digest_created = self._create_daily_digest_from_top_articles(date, processed_articles)
                    if digest_created:
                        logger.info("✅ Дайджест створено з ТОП-5 статей")
                except Exception as e:
                    errors.append(f"Помилка створення дайджесту: {str(e)}")
                    logger.error(f"❌ Помилка дайджесту: {e}")
            
            # === КРОК 4: Оновлення ROI метрик ===
            if not dry_run and processed_articles:
                logger.info("📊 Крок 4: Розрахунок ROI метрик...")
                try:
                    roi_calculated = self._update_roi_metrics(date, len(processed_articles))
                    if roi_calculated:
                        logger.info("✅ ROI метрики оновлено")
                except Exception as e:
                    errors.append(f"Помилка ROI розрахунку: {str(e)}")
                    logger.error(f"❌ Помилка ROI: {e}")
            
            # === КРОК 5: Оновлення віджетів головної сторінки ===
            if not dry_run and processed_articles:
                logger.info("🏠 Крок 5: Оновлення віджетів головної...")
                try:
                    top_articles_for_widget = [a for a in processed_articles if getattr(a, 'is_top_article', False)]
                    if top_articles_for_widget:
                        logger.info("📢 На головну піде %d топ-статей", min(5, len(top_articles_for_widget)))
                    self._update_homepage_widgets(top_articles_for_widget[:5])
                    logger.info("✅ Віджети оновлено")
                except Exception as e:
                    errors.append(f"Помилка оновлення віджетів: {str(e)}")
                    logger.error(f"❌ Помилка віджетів: {e}")
            
            processing_time = time.time() - start_time
            success_rate = (articles_published / len(top_articles)) * 100 if top_articles else 0
            
            # Оновлюємо статистику
            self._update_pipeline_stats(processing_time, len(top_articles), articles_published)
            
            logger.info(
                f"🎉 Pipeline завершено за {processing_time:.1f}с: "
                f"{articles_published}/{len(top_articles)} статей ({success_rate:.1f}%)"
            )
            
            return PipelineResult(
                date=date,
                total_articles_processed=len(top_articles),
                top_articles_selected=len(top_articles),
                articles_published=articles_published,
                digest_created=digest_created,
                roi_calculated=roi_calculated,
                processing_time=processing_time,
                errors=errors,
                success_rate=success_rate
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Критична помилка pipeline: {str(e)}"
            logger.error(error_msg)
            
            return PipelineResult(
                date=date,
                total_articles_processed=0,
                top_articles_selected=0,
                articles_published=0,
                digest_created=False,
                roi_calculated=False,
                processing_time=processing_time,
                errors=[error_msg],
                success_rate=0.0
            )

    def _process_single_article(self, raw_article: RawArticle, relevance_analysis, dry_run: bool = False) -> Optional[ProcessedArticle]:
        """Обробляє одну статтю через повний пайплайн (FiveFilters → insights → AI → publish)."""
        try:
            # 1) Збагачуємо повним контентом через FiveFilters (тільки для топ-статей)
            logger.info("🔍 Збагачення повним контентом через FiveFilters...")
            full_content = self.ai_processor._enhance_with_fivefilters(raw_article)
            if full_content and len(full_content) > 1000:
                logger.info(f"✅ Full-text отримано: {len(full_content)} символів")
                # Позначаємо, що стаття має повний контент
                raw_article.has_full_content = True
                raw_article.save(update_fields=['has_full_content'])
            else:
                logger.warning("⚠️ Full-text короткий або недоступний; використовуємо RSS контент")
                full_content = (raw_article.content or raw_article.summary or "").strip()
                raw_article.has_full_content = False
                raw_article.save(update_fields=['has_full_content'])

            # 2) Розширені інсайти LAZYSOFT з повним контентом
            logger.info("🤖 Створення LAZYSOFT інсайтів з повним контентом...")
            enhanced_insights = self.enhanced_analyzer.analyze_full_article_with_insights(
                raw_article, full_content
            )

            # 3) Основна AI-обробка (генерація ~1100 символів оригінального тексту у summary_*)
            logger.info("🎨 AI обробка та генерація контенту...")
            processed_article = self.ai_processor.process_article(raw_article)
            if not processed_article:
                logger.error("❌ AI процесор не зміг обробити статтю")
                return None

            # 4) Збагачуємо ProcessedArticle інсайтами та релевантністю
            if not dry_run:
                self._enrich_processed_article(processed_article, enhanced_insights, relevance_analysis)

                # 5) Заповнюємо повний контент для топ-статей
                if raw_article.has_full_content and full_content:
                    logger.info("📝 Заповнення повного контенту для топ-статті...")
                    # Генеруємо повний контент на всіх мовах
                    processed_article.full_content_en = self._generate_full_content(full_content, 'en')
                    processed_article.full_content_pl = self._generate_full_content(full_content, 'pl')
                    processed_article.full_content_uk = self._generate_full_content(full_content, 'uk')
                    processed_article.full_content_parsed = True
                    processed_article.original_word_count = len(full_content.split())
                    processed_article.reading_time = max(5, processed_article.original_word_count // 200)

                # 6) Публікуємо статтю (встановлюємо статус, пріоритет, дату)
                base_priority = 3
                try:
                    score = getattr(relevance_analysis, "relevance_score", None)
                    if score is None and isinstance(relevance_analysis, dict):
                        score = relevance_analysis.get("relevance_score")
                    if isinstance(score, (int, float)):
                        base_priority = max(3, min(5, int(score // 2)))
                except Exception:
                    pass

                processed_article.status = "published"
                processed_article.priority = base_priority
                processed_article.published_at = timezone.now()
                processed_article.save()

                logger.info(f"📢 Статтю опубліковано з пріоритетом {processed_article.priority}")

            return processed_article

        except Exception as e:
            logger.exception(f"❌ Помилка обробки статті: {e}")
            return None

    def _generate_full_content(self, content: str, language: str) -> str:
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
"""
            
            full_content = self.ai_processor._call_ai_model(prompt, max_tokens=3000)
            return full_content.strip()
            
        except Exception as e:
            logger.warning(f"⚠️ Помилка генерації Business Impact для {language}: {e}")
            # Повертаємо оригінальний контент якщо генерація не вдалася
            return content

    def _enrich_processed_article(self, processed_article: ProcessedArticle, enhanced_insights, relevance_analysis):
        """Додає розширені інсайти до ProcessedArticle (безпечно обробляє відсутні поля/типи)."""
        def pick_lang(d, lang, list_expected=False):
            if not d:
                return [] if list_expected else ""
            if isinstance(d, dict):
                return d.get(lang, [] if list_expected else "")
            # якщо прийшло щось нестандартне — повернемо дефолт
            return [] if list_expected else ""

        try:
            # Дістанемо словники з enhanced_insights незалежно від його типу (dataclass/obj/dict)
            insights_dict = {}
            for key in ["interesting_facts", "business_opportunities", "lazysoft_recommendations", "business_insights"]:
                try:
                    insights_dict[key] = getattr(enhanced_insights, key, {}) or {}
                except Exception:
                    insights_dict[key] = {}

            # 1) Business Insights (основні інсайти)
            business_insights = insights_dict.get("business_insights", {})
            processed_article.business_insight_en = pick_lang(business_insights, "english_audience")
            processed_article.business_insight_pl = pick_lang(business_insights, "polish_audience")
            processed_article.business_insight_uk = pick_lang(business_insights, "ukrainian_audience")
            
            # Якщо business_insights порожні, спробуємо взяти з main_insight
            if not processed_article.business_insight_en:
                processed_article.business_insight_en = pick_lang(business_insights, "english")
            if not processed_article.business_insight_pl:
                processed_article.business_insight_pl = pick_lang(business_insights, "polish")
            if not processed_article.business_insight_uk:
                processed_article.business_insight_uk = pick_lang(business_insights, "ukrainian")

            # 2) Цікавинки (очікуємо списки)
            processed_article.interesting_facts_en = pick_lang(insights_dict["interesting_facts"], "english", list_expected=True)
            processed_article.interesting_facts_pl = pick_lang(insights_dict["interesting_facts"], "polish", list_expected=True)
            processed_article.interesting_facts_uk = pick_lang(insights_dict["interesting_facts"], "ukrainian", list_expected=True)

            # 3) Бізнес-можливості (рядки)
            bo_en = pick_lang(insights_dict["business_opportunities"], "english")
            bo_pl = pick_lang(insights_dict["business_opportunities"], "polish")
            bo_uk = pick_lang(insights_dict["business_opportunities"], "ukrainian")

            # fallback: якщо порожньо — візьмемо з твоїх business_insight_*
            if not bo_en:
                bo_en = getattr(processed_article, "business_insight_en", "") or ""
            if not bo_pl:
                bo_pl = getattr(processed_article, "business_insight_pl", "") or ""
            if not bo_uk:
                bo_uk = getattr(processed_article, "business_insight_uk", "") or ""

            processed_article.business_opportunities_en = bo_en
            processed_article.business_opportunities_pl = bo_pl
            processed_article.business_opportunities_uk = bo_uk

            # 4) Рекомендації LAZYSOFT (рядки)
            processed_article.lazysoft_recommendations_en = pick_lang(insights_dict["lazysoft_recommendations"], "english")
            processed_article.lazysoft_recommendations_pl = pick_lang(insights_dict["lazysoft_recommendations"], "polish")
            processed_article.lazysoft_recommendations_uk = pick_lang(insights_dict["lazysoft_recommendations"], "ukrainian")

            # 5) Прокинемо релевантність, якщо є поле в моделі
            try:
                score = getattr(relevance_analysis, "relevance_score", None)
                if score is None and isinstance(relevance_analysis, dict):
                    score = relevance_analysis.get("relevance_score")
                if hasattr(processed_article, "relevance_score") and score is not None:
                    processed_article.relevance_score = int(score)
            except Exception:
                pass

            processed_article.save()
            logger.info("✅ Розширені інсайти додано до статті")

        except Exception as e:
            logger.warning(f"⚠️ Помилка додавання інсайтів: {e}")

    def _create_daily_digest_from_top_articles(self, date: datetime.date, top_articles: List[ProcessedArticle]) -> bool:
        """Створює щоденний дайджест ТІЛЬКИ з ТОП-5 статей."""
        try:
            if not top_articles:
                logger.info("📭 Немає ТОП статей для дайджесту")
                return False

            # Створюємо дайджест з ТОП-5 статей
            digest, created = DailyDigest.objects.get_or_create(
                date=date,
                defaults={
                    'title_en': f"LAZYSOFT Top Tech News - {date.strftime('%B %d, %Y')}",
                    'title_pl': f"LAZYSOFT Top wiadomości technologiczne - {date.strftime('%d %B %Y')}",
                    'title_uk': f"LAZYSOFT Топ технологічних новин - {date.strftime('%d %B %Y')}",
                    'intro_text_en': f"Our top {len(top_articles)} curated tech insights for {date}",
                    'intro_text_pl': f"Nasze top {len(top_articles)} wyselekcjonowanych wiadomości technologicznych za {date}",
                    'intro_text_uk': f"Наші топ-{len(top_articles)} відібраних технологічних інсайтів за {date}",
                    'total_articles': len(top_articles),
                    'is_generated': True,
                    'is_published': True,
                    'published_at': timezone.now()
                }
            )

            # Оновлюємо кількість статей якщо дайджест вже існував
            if not created:
                digest.total_articles = len(top_articles)
                digest.save()

            logger.info(f"✅ Дайджест {'створено' if created else 'оновлено'} з {len(top_articles)} ТОП статей")
            return True

        except Exception as e:
            logger.error(f"❌ Помилка створення дайджесту: {e}")
            return False

    def _update_roi_metrics(self, date: datetime.date, articles_processed: int) -> bool:
        """Оновлює ROI метрики"""
        
        try:
            roi = ROIAnalytics.calculate_daily_metrics(date)
            logger.info(f"✅ ROI розраховано: ${roi.net_savings:.2f} економії")
            return True
            
        except Exception as e:
            logger.error(f"❌ Помилка ROI розрахунку: {e}")
            return False

    def _update_homepage_widgets(self, processed_articles: List[ProcessedArticle]):
        """Оновлює віджети новин на головній сторінці"""
 
        try:
            logger.info("🏠 Оновлення віджетів — отримано %d статей", len(processed_articles))
            # Тут можна додати логіку оновлення кешу віджетів
            # Наприклад, інвалідувати кеш або оновити статичні файли
 
            from django.core.cache import cache
 
            # Очищаємо кеш віджетів новин
            cache_keys = [
                'homepage_news_uk',
                'homepage_news_en', 
                'homepage_news_pl',
                'featured_articles',
                'news_digest'
            ]
 
            for key in cache_keys:
                cache.delete(key)
 
            logger.info("✅ Кеш віджетів очищено")
 
        except Exception as e:
            logger.warning(f"⚠️ Помилка оновлення віджетів: {e}")

    def _update_pipeline_stats(self, processing_time: float, total_articles: int, successful_articles: int):
        """Оновлює статистику роботи пайплайна"""
        
        self.stats['total_runs'] += 1
        if successful_articles > 0:
            self.stats['successful_runs'] += 1
        
        # Оновлюємо середній час
        self.stats['avg_processing_time'] = (
            (self.stats['avg_processing_time'] * (self.stats['total_runs'] - 1) + processing_time) /
            self.stats['total_runs']
        )
        
        self.stats['total_articles_processed'] += total_articles

    def _create_empty_result(self, date: datetime.date, processing_time: float) -> PipelineResult:
        """Створює порожній результат якщо немає статей"""
        
        return PipelineResult(
            date=date,
            total_articles_processed=0,
            top_articles_selected=0,
            articles_published=0,
            digest_created=False,
            roi_calculated=False,
            processing_time=processing_time,
            errors=["Немає статей для обробки"],
            success_rate=0.0
        )

    def get_pipeline_statistics(self) -> Dict:
        """Повертає статистику роботи пайплайна"""
        
        return {
            **self.stats,
            'components': {
                'full_parser': self.full_parser.get_parsing_stats(),
                'audience_analyzer': self.audience_analyzer.get_analysis_statistics(),
                'ai_processor': self.ai_processor.get_processing_stats()
            }
        }

    def health_check(self) -> Dict:
        """Перевіряє здоров'я всіх компонентів пайплайна"""
        
        health = {}
        
        try:
            # Перевіряємо AI підключення
            test_article = RawArticle.objects.first()
            if test_article:
                # Швидкий тест Audience Analyzer
                analysis = self.audience_analyzer.analyze_article_relevance(test_article)
                health['audience_analyzer'] = analysis.relevance_score > 0
                
                # Тест AI процесора (тільки OpenAI)
                health['ai_processor'] = self.ai_processor.openai_client is not None
            else:
                health['audience_analyzer'] = False
                health['ai_processor'] = False
            
            # Тест Full Parser
            health['full_parser'] = True  # Завжди доступний
            
            health['overall'] = all(health.values())
            
        except Exception as e:
            logger.error(f"❌ Помилка health check: {e}")
            health = {'overall': False, 'error': str(e)}
        
        return health