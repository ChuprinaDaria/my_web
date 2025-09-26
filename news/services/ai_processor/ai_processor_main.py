import time
from typing import Dict, Optional
from django.utils import timezone
from django.db.models import Sum, Q, F
from datetime import datetime, timedelta

from .ai_processor_content import AIContentProcessor
from .ai_processor_helpers import AIProcessorHelpers
from news.models import RawArticle, ProcessedArticle, AIProcessingLog
from .ai_processor_database import AIProcessorDatabase 

class AINewsProcessor(AIContentProcessor, AIProcessorHelpers, AIProcessorDatabase):
    """Головний AI процесор для новин - основна обробка"""

    def process_article(self, raw_article: RawArticle) -> Optional[ProcessedArticle]:
        """Обробляє одну сиру статтю через AI з FiveFilters збагаченням"""
        start_time = time.time()
        self.logger.info(f"[AI] Обробка статті: {raw_article.title[:50]}...")

        try:
            # 0) НОВИЙ КРОК: Збагачення FiveFilters ПЕРЕД AI обробкою
            enhanced_content = self._enhance_with_fivefilters(raw_article)
            
            # 1) Аналіз + категоризація (тепер на збагаченому контенті)
            category_info = self._categorize_article(raw_article)
            self.logger.info(f"[AI] Категорія визначена: {category_info['category']}")

            # 2) Тримовний контент (використовує збагачений контент)
            processed_content = self._create_multilingual_content(raw_article, category_info)
            self.logger.info("[AI] Тримовний контент створено ✅")

            # 3) Стокові зображення замість AI генерації (як ти хотіла)
            from news.services.stock_image_service import stock_image_service

            self.logger.info("[IMAGE] Пошук стокового зображення...")

            # Витягуємо ключові слова з контенту
            content_keywords = self._extract_keywords_from_content(
                raw_article.content or raw_article.summary or ""
            )

            try:
                image_url = stock_image_service.get_image_for_article(
                    title=raw_article.title,
                    category=category_info.get('category_slug', 'general'),
                    keywords=content_keywords
                )
                
                processed_content["ai_image_url"] = image_url
                
                if image_url:
                    self.logger.info(f"[IMAGE] Стокове зображення знайдено: {image_url}")
                else:
                    self.logger.warning("[IMAGE] Стокове зображення не знайдено")
                    
            except Exception as img_err:
                self.logger.error(f"[IMAGE] Помилка пошуку стокового зображення: {img_err}")
                processed_content["ai_image_url"] = None

            # 4) Зберігаємо оброблену статтю (решта коду залишається)
            processed_article = self._save_processed_article(raw_article, processed_content)

            # 4.1) Записуємо зображення
            image_url_to_save = processed_content.get("ai_image_url")
            self.logger.info(f"[IMAGE] Збереження зображення: {image_url_to_save}")
            if image_url_to_save:
                processed_article.ai_image_url = image_url_to_save
                processed_article.save(update_fields=["ai_image_url"])
                self.logger.info(f"[IMAGE] ✅ Зображення збережено: {processed_article.ai_image_url}")
            else:
                self.logger.warning("[IMAGE] ⚠️ Немає URL для збереження")

            self.logger.info("[AI] Статтю збережено в базу ✅")

            # 5) Статистика
            processing_time = time.time() - start_time
            processed_content["processing_time"] = processing_time
            self._log_ai_processing(raw_article, "full_processing", processed_content)

            # Позначаємо як оброблений
            raw_article.is_processed = True
            raw_article.save(update_fields=["is_processed"])

            self.stats["processed"] += 1
            self.stats["successful"] += 1
            self.stats["total_time"] += processing_time
            self.stats["total_cost"] += processed_content.get("cost", 0.0)

            self.logger.info(
                "[SUCCESS] Статтю оброблено за %.2fs, вартість: $%.4f",
                processing_time,
                processed_content.get("cost", 0.0),
            )

            return processed_article

        except Exception as e:
            self.stats["failed"] += 1
            error_msg = str(e)

            raw_article.processing_attempts = (raw_article.processing_attempts or 0) + 1
            raw_article.error_message = error_msg
            raw_article.save(update_fields=["processing_attempts", "error_message"])

            self._log_ai_processing(raw_article, "error", {"error": error_msg})
            self.logger.error(f"[ERROR] Помилка обробки статті: {error_msg}")
            return None

    def process_batch(self, limit: int = 10, category: str = None) -> Dict:
        """Обробляє пакет необроблених статей"""
        
        self.logger.info(f"🚀 Пакетна обробка: до {limit} статей")
        
        # Отримуємо необроблені статті
        queryset = RawArticle.objects.filter(
            is_processed=False,
            is_duplicate=False
        ).order_by('-published_at')
        
        if category:
            queryset = queryset.filter(source__category=category)
        
        articles = list(queryset[:limit])
        
        if not articles:
            self.logger.info("📭 Немає статей для обробки")
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'total_cost': 0
            }
        
        self.logger.info(f"📄 Знайдено {len(articles)} статей для обробки")
        
        # Обробляємо кожну статтю
        results = []
        for article in articles:
            result = self.process_article(article)
            results.append(result)
            
            # Невелика пауза між запитами
            time.sleep(1)
        
        # Фінальна статистика
        successful = len([r for r in results if r is not None])
        
        self.logger.info(
            f"🎯 Пакетна обробка завершена: {successful}/{len(articles)} успішних"
        )
        
        return {
            'processed': len(articles),
            'successful': successful,
            'failed': len(articles) - successful,
            'total_cost': self.stats['total_cost'],
            'total_time': self.stats['total_time']
        }

    def process_top5_by_engagement(self, days: int = 7) -> Dict:
        """Обробляє топ-5 статей по engagement за останні дні"""
        
        cutoff = timezone.now() - timedelta(days=days)

        # 1) топ категорії за переглядами
        top_cats = (ProcessedArticle.objects
            .filter(published_at__gte=cutoff, status='published')
            .values('category__slug')
            .annotate(total_views=Sum(F('views_count_uk') + F('views_count_en') + F('views_count_pl')))
            .order_by('-total_views')[:3])

        cat_slugs = [c['category__slug'] for c in top_cats] or ['general']

        # 2) свіжі RawArticle з цих категорій (не оброблені)
        queryset = (RawArticle.objects
            .filter(is_processed=False, is_duplicate=False, source__category__in=cat_slugs)
            .order_by('-published_at')[:5])

        results = []
        for article in queryset:
            result = self.process_article(article)
            results.append(result)
            time.sleep(1)

        success = len([r for r in results if r])
        return {
            'processed': len(results),
            'successful': success,
            'failed': len(results) - success
        }

    def _log_ai_processing(self, raw_article: RawArticle, log_type: str, data):
        """Логує AI обробку"""
        try:
            # БЕЗПЕЧНЕ ОТРИМАННЯ ЗНАЧЕНЬ
            if isinstance(data, dict):
                ai_model = data.get('ai_model_used', self.preferred_model)
                processing_time = data.get('processing_time', 0)
                cost = data.get('cost', 0)
                error_msg = data.get('error', '')
                success = 'error' not in data
            else:
                # Якщо data це ProcessedContent або інший об'єкт
                ai_model = getattr(data, 'ai_model_used', self.preferred_model)
                processing_time = getattr(data, 'processing_time', 0)
                cost = getattr(data, 'cost', 0)
                error_msg = ''
                success = True
            
            AIProcessingLog.objects.create(
                article=raw_article,
                log_type=log_type,
                model_used=ai_model,
                processing_time=processing_time,
                cost=cost,
                success=success,
                input_data={'title': raw_article.title[:100]},
                output_data={'status': 'processed' if success else 'error'},
                error_message=error_msg
            )
        except Exception as e:
            self.logger.error(f"[ERROR] Помилка логування: {e}")


    def _enhance_with_fivefilters(self, raw_article: RawArticle) -> str:
        """Збагачує статтю повним текстом через FiveFilters"""
        
        # Перевіряємо чи не збагачено вже
        original_length = len(raw_article.content or "")
        
        # Якщо контент вже довгий - можливо вже збагачено
        if original_length > 1500:
            self.logger.info(f"[FIVEFILTERS] Контент вже довгий ({original_length} симв), вважаємо повним")
            # Встановлюємо флаг повного контенту
            raw_article.has_full_content = True
            raw_article.save(update_fields=['has_full_content'])
            return raw_article.content or ""
        
        try:
            from news.services.fulltext_extractor import FullTextExtractor
            
            self.logger.info(f"[FIVEFILTERS] Збагачення: {raw_article.original_url}")
            
            extractor = FullTextExtractor()
            full_content = extractor.extract_article(raw_article.original_url)
            
            if full_content and len(full_content) > original_length:
                improvement = len(full_content) - original_length
                
                # ЗБЕРІГАЄМО збагачений контент в БД
                raw_article.content = full_content
                raw_article.has_full_content = True
                raw_article.save(update_fields=['content', 'has_full_content'])
                
                self.logger.info(f"[FIVEFILTERS] ✅ Збагачено: +{improvement} символів ({len(full_content)} total)")
                return full_content
            else:
                self.logger.warning(f"[FIVEFILTERS] ⚠️ Не вдалося збагатити або контент коротший")
                raw_article.has_full_content = False
                raw_article.save(update_fields=['has_full_content'])
                return raw_article.content or raw_article.summary or ""
                
        except Exception as e:
            self.logger.warning(f"[FIVEFILTERS] ❌ Помилка: {e}")
            raw_article.has_full_content = False
            raw_article.save(update_fields=['has_full_content'])
            return raw_article.content or raw_article.summary or ""


    def _extract_keywords_from_content(self, content: str) -> list:
        """Витягує ключові слова з контенту для пошуку зображень"""
        import re
        
        if not content:
            return []
        
        # Стоп-слова
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could'
        }
        
        # Витягуємо слова
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        
        # Рахуємо частоту
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Повертаємо топ-5 найчастіших
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:5]]
