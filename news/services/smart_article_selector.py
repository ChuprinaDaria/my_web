import logging
from typing import List, Dict, Optional
from django.conf import settings
from ..models import RawArticle, NewsCategory

logger = logging.getLogger(__name__)

class SmartArticleSelector:
    """Розумний селектор кращих статей через AI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def select_top_articles(self, limit: int = 10, category: Optional[str] = None) -> List[RawArticle]:
        """
        Вибирає топ статті для обробки
        
        Args:
            limit: Кількість статей для вибору
            category: Фільтр по категорії
            
        Returns:
            Список найкращих статей для обробки
        """
        
        # Базовий запит
        queryset = RawArticle.objects.filter(
            is_processed=False,
            is_duplicate=False
        ).select_related('source')
        
        # Фільтр по категорії
        if category:
            queryset = queryset.filter(source__category=category)
        
        # Сортування по якості
        articles = list(queryset.order_by('-published_at')[:limit * 2])  # Беремо більше для аналізу
        
        if not articles:
            self.logger.warning("Немає статей для селекції")
            return []
        
        # Простий алгоритм селекції поки що
        # TODO: Додати AI-аналіз релевантності
        selected = self._simple_quality_filter(articles, limit)
        
        self.logger.info(f"📊 Вибрано {len(selected)} з {len(articles)} статей")
        
        return selected
    
    def _simple_quality_filter(self, articles: List[RawArticle], limit: int) -> List[RawArticle]:
        """Простий фільтр якості статей"""
        
        scored_articles = []
        
        for article in articles:
            score = 0
            
            # Довжина контенту
            content_length = len(article.content or article.summary or "")
            if content_length > 1000:
                score += 3
            elif content_length > 500:
                score += 2
            elif content_length > 200:
                score += 1
            
            # Свіжість
            from django.utils import timezone
            hours_old = (timezone.now() - article.published_at).total_seconds() / 3600
            if hours_old < 6:
                score += 2
            elif hours_old < 24:
                score += 1
            
            # Якість джерела (можна розширити)
            if article.source.language == 'en':  # Англійські джерела мають пріоритет
                score += 1
            
            scored_articles.append((article, score))
        
        # Сортуємо по скору і беремо топ
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        
        return [article for article, score in scored_articles[:limit]]