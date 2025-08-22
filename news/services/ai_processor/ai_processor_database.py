from typing import Union, Dict, Any
from news.models import RawArticle, ProcessedArticle, NewsCategory
from .ai_processor_base import AINewsProcessor


class AIProcessorDatabase:
    """Модуль для збереження оброблених статей в базу даних"""
    processor = AINewsProcessor()
    print("CLASS:", processor.__class__)
    print("MRO:", [c.__name__ for c in processor.__class__.__mro__])
    print("HAS SAVE:", hasattr(processor, "_save_processed_article"))

    def _save_processed_article(self, raw_article: RawArticle, content: Union[Dict, Any]) -> ProcessedArticle:
        """Зберігає оброблену статтю (працює і з dict, і з об'єктом)."""
        
        # Категорія
        try:
            category = NewsCategory.objects.get(slug=self._safe_get_value(content, "category_slug", "general"))
        except NewsCategory.DoesNotExist:
            category = NewsCategory.objects.get(slug="general")

        # Значення з фолбеками
        title_en = self._safe_get_value(content, "title_en", raw_article.title or "")
        title_pl = self._safe_get_value(content, "title_pl", raw_article.title or "")
        title_uk = self._safe_get_value(content, "title_uk", raw_article.title or "")

        summary_en = self._safe_get_value(content, "summary_en", (raw_article.summary or raw_article.content or "")[:160])
        summary_pl = self._safe_get_value(content, "summary_pl", summary_en)
        summary_uk = self._safe_get_value(content, "summary_uk", summary_en)

        business_insight_en = self._safe_get_value(content, "business_insight_en", "")
        business_insight_pl = self._safe_get_value(content, "business_insight_pl", "")
        business_insight_uk = self._safe_get_value(content, "business_insight_uk", "")

        local_context_en = self._safe_get_value(content, "local_context_en", "")
        local_context_pl = self._safe_get_value(content, "local_context_pl", "")
        local_context_uk = self._safe_get_value(content, "local_context_uk", "")

        key_takeaways_en = self._safe_get_value(content, "key_takeaways_en", []) or []
        key_takeaways_pl = self._safe_get_value(content, "key_takeaways_pl", []) or []
        key_takeaways_uk = self._safe_get_value(content, "key_takeaways_uk", []) or []

        # CTA (завжди не пусто)
        cta_title_en = self._safe_get_value(content, "cta_title_en", "Get Expert Analysis")
        cta_title_pl = self._safe_get_value(content, "cta_title_pl", "Otrzymaj ekspercką analizę")
        cta_title_uk = self._safe_get_value(content, "cta_title_uk", "Отримати експертний аналіз")

        cta_description_en = self._safe_get_value(content, "cta_description_en", "Contact us for personalized business consultation")
        cta_description_pl = self._safe_get_value(content, "cta_description_pl", "Skontaktuj się z nami w sprawie spersonalizowanej konsultacji biznesowej")
        cta_description_uk = self._safe_get_value(content, "cta_description_uk", "Звʼяжіться з нами для персоналізованої бізнес-консультації")

        cta_buttons = self._safe_get_value(content, "cta_buttons", []) or self._generate_cta_buttons(self._safe_get_value(content, "category_slug", "general"))

        # SEO (гарантовано заповнені)
        meta_title_en = self._safe_get_value(content, "meta_title_en", title_en[:60])
        meta_title_pl = self._safe_get_value(content, "meta_title_pl", title_pl[:60])
        meta_title_uk = self._safe_get_value(content, "meta_title_uk", title_uk[:60])

        meta_description_en = self._safe_get_value(content, "meta_description_en", summary_en[:160])
        meta_description_pl = self._safe_get_value(content, "meta_description_pl", summary_pl[:160])
        meta_description_uk = self._safe_get_value(content, "meta_description_uk", summary_uk[:160])

        # Промпти з опису (твоя вимога)
        ai_image_prompt_en = self._safe_get_value(content, "ai_image_prompt_en", title_en)
        ai_image_prompt_pl = self._safe_get_value(content, "ai_image_prompt_pl", title_pl)
        ai_image_prompt_uk = self._safe_get_value(content, "ai_image_prompt_uk", title_uk)
        
        ai_image_url = self._safe_get_value(content, "ai_image_url", "")

        processed_article = ProcessedArticle.objects.create(
            raw_article=raw_article,
            category=category,

            title_en=title_en, 
            title_pl=title_pl, 
            title_uk=title_uk,
            
            summary_en=summary_en, 
            summary_pl=summary_pl, 
            summary_uk=summary_uk,

            business_insight_en=business_insight_en,
            business_insight_pl=business_insight_pl,
            business_insight_uk=business_insight_uk,

            local_context_en=local_context_en,
            local_context_pl=local_context_pl,
            local_context_uk=local_context_uk,

            key_takeaways_en=key_takeaways_en,
            key_takeaways_pl=key_takeaways_pl,
            key_takeaways_uk=key_takeaways_uk,

            cta_title_en=cta_title_en,
            cta_title_pl=cta_title_pl,
            cta_title_uk=cta_title_uk,

            cta_description_en=cta_description_en,
            cta_description_pl=cta_description_pl,
            cta_description_uk=cta_description_uk,

            cta_buttons=cta_buttons,

            meta_title_en=meta_title_en,
            meta_title_pl=meta_title_pl,
            meta_title_uk=meta_title_uk,
            
            meta_description_en=meta_description_en,
            meta_description_pl=meta_description_pl,
            meta_description_uk=meta_description_uk,

            ai_image_url=ai_image_url,
            ai_image_prompt_en=ai_image_prompt_en,
            

            priority=self._safe_get_value(content, "priority", 2),
            status="draft",
            ai_model_used=self._safe_get_value(content, "ai_model_used", ""),
            ai_cost=self._safe_get_value(content, "cost", 0.0),
            ai_processing_time=self._safe_get_value(content, "processing_time", 0.0),
        )

        self.logger.info(f"[SAVE] ProcessedArticle створено: ID {processed_article.id}")
        return processed_article
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
            category = NewsCategory.objects.get(slug=self._safe_get_value(content, "category_slug", "general"))
        except NewsCategory.DoesNotExist:
            category = NewsCategory.objects.get(slug="general")
        
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
            article_data[f'local_context_{lang}'] = self._safe_get_value(
                content, f"local_context_{lang}", ""
            )
            article_data[f'key_takeaways_{lang}'] = self._safe_get_value(
                content, f"key_takeaways_{lang}", []
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