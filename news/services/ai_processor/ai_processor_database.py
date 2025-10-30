from typing import Union, Dict, Any
from news.models import RawArticle, ProcessedArticle, NewsCategory
from .ai_processor_base import AINewsProcessor


class AIProcessorDatabase:
    """Модуль для збереження оброблених статей в базу даних"""

    def _save_processed_article(self, raw_article: RawArticle, content: Union[Dict, Any]) -> ProcessedArticle:
        """
        Єдиний шлях збереження: будуємо валідований словник і тільки потім створюємо модель.
        Якщо валідація не проходить – автоматичний fallback у _create_processed_article_dict.
        """

        try:
            # 1) Сконструювати словник з валідацією (використовує _validate_content_before_save)
            self.logger.info("[SAVE] Створення словника article_data...")
            article_data = self._create_processed_article_dict(raw_article, content)
            self.logger.info(f"[SAVE] article_data створено з {len(article_data)} полями")

            # 2) Створити запис (article_data вже містить усі фолбеки та коректні значення)
            self.logger.info("[SAVE] Створення ProcessedArticle в БД...")
            processed_article = ProcessedArticle.objects.create(**article_data)

            self.logger.info(f"[SAVE] ✅ ProcessedArticle створено: ID {processed_article.id}")
            return processed_article

        except Exception as save_error:
            self.logger.exception(f"[SAVE] ❌ КРИТИЧНА ПОМИЛКА при збереженні ProcessedArticle: {save_error}")
            self.logger.error(f"[SAVE] article_data keys: {list(article_data.keys()) if 'article_data' in locals() else 'NOT CREATED'}")
            raise
    def _attach_featured_image_from_url(self, article, url: str):
        if not url or not hasattr(article, "featured_image"):
            return
        try:
            import requests
            from django.core.files.base import ContentFile
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            name = f"ai_{article.slug}.png"
            article.featured_image.save(name, ContentFile(r.content), save=True)
        except Exception as e:
            self.logger.warning(f"[IMAGE] Не вдалося зберегти featured_image: {e}")
            
    def _validate_content_before_save(self, content: Union[Dict, Any]) -> bool:
        """Валідує контент перед збереженням"""
        required_fields = [
            "title_en", "title_pl", "title_uk",
            "summary_en", "summary_pl", "summary_uk",
            "business_insight_en", "business_insight_pl", "business_insight_uk"
        ]
        
        missing_fields = []
        for field in required_fields:
            value = self._safe_get_value(content, field, "")
            if not value or len(str(value).strip()) < 5:
                missing_fields.append(field)
        
        if missing_fields:
            self.logger.warning(f"[VALIDATION] Відсутні або короткі поля: {missing_fields}")
            return False
        
        return True

    def _create_processed_article_dict(self, raw_article: RawArticle, content: Union[Dict, Any]) -> Dict:
        """Створює словник для ProcessedArticle з валідацією"""
        
        # Базова валідація
        if not self._validate_content_before_save(content):
            self.logger.warning("[VALIDATION] Контент не пройшов валідацію, використовуємо fallback")
            # Тут можна додати логіку створення fallback контенту
        
        # Категорія
        try:
            slug = self._safe_get_value(content, "category_slug", "general")
            try:
                category = NewsCategory.objects.get(slug=slug)
            except NewsCategory.DoesNotExist:
                # Падаємо назад на 'general'; якщо її немає — створимо мінімально необхідну
                try:
                    category = NewsCategory.objects.get(slug="general")
                except NewsCategory.DoesNotExist:
                    category, _ = NewsCategory.objects.get_or_create(
                        slug="general",
                        defaults={
                            "name_en": "General",
                            "name_pl": "Ogólne",
                            "name_uk": "Загальне",
                            "description_en": "General technology news",
                            "description_pl": "Ogólne wiadomości technologiczne",
                            "description_uk": "Загальні технологічні новини",
                        },
                    )
        except Exception:
            # Абсолютний fallback на випадок інших помилок
            category, _ = NewsCategory.objects.get_or_create(
                slug="general",
                defaults={
                    "name_en": "General",
                    "name_pl": "Ogólne",
                    "name_uk": "Загальне",
                    "description_en": "General technology news",
                    "description_pl": "Ogólne wiadomości technologiczne",
                    "description_uk": "Загальні технологічні новини",
                },
            )
        
        # Створюємо словник з усіма полями
        article_data = {
            'raw_article': raw_article,
            'category': category,
            'status': 'draft',
            'priority': self._safe_get_value(content, "priority", 2),
            'ai_model_used': self._safe_get_value(content, "ai_model_used", self.preferred_model),
            'ai_cost': self._safe_get_value(content, "cost", 0.0),
            'ai_processing_time': self._safe_get_value(content, "processing_time", 0.0),
        }
        
        # Тримовні поля
        for lang in ['en', 'pl', 'uk']:
            article_data[f'title_{lang}'] = self._safe_get_value(
                content, f"title_{lang}", raw_article.title or ""
            )
            article_data[f'summary_{lang}'] = self._safe_get_value(
                content, f"summary_{lang}", 
                (raw_article.summary or raw_article.content or "")[:160]
            )
            article_data[f'business_insight_{lang}'] = self._safe_get_value(
                content, f"business_insight_{lang}", ""
            )
            article_data[f'business_opportunities_{lang}'] = self._safe_get_value(
                content, f"business_opportunities_{lang}", ""
            )
            article_data[f'lazysoft_recommendations_{lang}'] = self._safe_get_value(
                content, f"lazysoft_recommendations_{lang}", ""
            )
            article_data[f'local_context_{lang}'] = self._safe_get_value(
                content, f"local_context_{lang}", ""
            )
            article_data[f'key_takeaways_{lang}'] = self._safe_get_value(
                content, f"key_takeaways_{lang}", []
            ) or []
            
            # Нові поля для детального аналізу
            article_data[f'interesting_facts_{lang}'] = self._safe_get_value(
                content, f"interesting_facts_{lang}", []
            ) or []
            
            article_data[f'implementation_steps_{lang}'] = self._safe_get_value(
                content, f"implementation_steps_{lang}", []
            ) or []
            
            # CTA
            article_data[f'cta_title_{lang}'] = self._safe_get_value(
                content, f"cta_title_{lang}", 
                {"en": "Get Expert Analysis", "pl": "Otrzymaj ekspercką analizę", "uk": "Отримати експертний аналіз"}[lang]
            )
            article_data[f'cta_description_{lang}'] = self._safe_get_value(
                content, f"cta_description_{lang}", 
                {
                    "en": "Contact us for personalized business consultation",
                    "pl": "Skontaktuj się z nami w sprawie spersonalizowanej konsultacji biznesowej",
                    "uk": "Звʼяжіться з нами для персоналізованої бізнес-консультації"
                }[lang]
            )
            
            # SEO
            article_data[f'meta_title_{lang}'] = self._safe_get_value(
                content, f"meta_title_{lang}", article_data[f'title_{lang}'][:60]
            )
            article_data[f'meta_description_{lang}'] = self._safe_get_value(
                content, f"meta_description_{lang}", article_data[f'summary_{lang}'][:160]
            )
            
            # AI Image промпти
            article_data[f'ai_image_prompt_{lang}'] = self._safe_get_value(
                content, f"ai_image_prompt_{lang}", article_data[f'title_{lang}']
            )
        
        # CTA кнопки
        article_data['cta_buttons'] = self._safe_get_value(
            content, "cta_buttons", []
        ) or self._generate_cta_buttons(self._safe_get_value(content, "category_slug", "general"))
        
        # AI зображення
        article_data['ai_image_url'] = self._safe_get_value(content, "ai_image_url", "")
        
        return article_data

    def _bulk_create_processed_articles(self, articles_data: list) -> list:
        """Масове створення ProcessedArticle записів"""
        processed_articles = []
        
        for article_data in articles_data:
            try:
                processed_article = ProcessedArticle(**article_data)
                processed_articles.append(processed_article)
            except Exception as e:
                self.logger.error(f"[BULK] Помилка підготовки статті: {e}")
        
        if processed_articles:
            try:
                created_articles = ProcessedArticle.objects.bulk_create(
                    processed_articles, batch_size=50
                )
                self.logger.info(f"[BULK] Створено {len(created_articles)} статей")
                return created_articles
            except Exception as e:
                self.logger.error(f"[BULK] Помилка масового створення: {e}")
                return []
        
        return []

    def _update_raw_article_status(self, raw_article: RawArticle, success: bool = True, error_message: str = ""):
        """Оновлює статус сирої статті після обробки"""
        raw_article.is_processed = success
        raw_article.processing_attempts = (raw_article.processing_attempts or 0) + 1
        
        if not success:
            raw_article.error_message = error_message
            raw_article.save(update_fields=["is_processed", "processing_attempts", "error_message"])
        else:
            raw_article.error_message = ""
            raw_article.save(update_fields=["is_processed", "processing_attempts", "error_message"])
        
        self.logger.info(f"[STATUS] RawArticle ID {raw_article.id} статус оновлено: processed={success}")