# news/services/stock_image_service.py
"""
Сервіс для отримання стокових зображень з безкоштовних API
"""

import requests
import logging
from typing import Optional, Dict, List
from django.conf import settings
from django.core.cache import cache
import hashlib

logger = logging.getLogger(__name__)


class StockImageService:
    """Сервіс для пошуку та отримання стокових зображень"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 15
        
        # API ключі з settings
        self.unsplash_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', None)
        self.pexels_key = getattr(settings, 'PEXELS_API_KEY', None)
        self.pixabay_key = getattr(settings, 'PIXABAY_API_KEY', None)
        
        # Налаштування кешування (30 днів)
        self.cache_timeout = 60 * 60 * 24 * 30
        
    def get_image_for_article(self, 
                            title: str, 
                            category: str = "general", 
                            keywords: List[str] = None) -> Optional[str]:
        """
        Головний метод - шукає підходяще зображення для статті
        
        Args:
            title: Заголовок статті
            category: Категорія новини
            keywords: Додаткові ключові слова
            
        Returns:
            URL зображення або None
        """
        logger.info(f"🖼️ Пошук зображення для статті: {title[:50]}...")
        
        # Формуємо пошукові запити
        search_queries = self._build_search_queries(title, category, keywords)
        
        # Кешування по хешу запиту
        cache_key = self._get_cache_key(search_queries[0])
        cached_url = cache.get(cache_key)
        if cached_url:
            logger.info("✅ Зображення знайдено в кеші")
            return cached_url
        
        # Пробуємо різні API по черзі
        for query in search_queries:
            image_url = self._try_all_apis(query)
            if image_url:
                # Кешуємо результат
                cache.set(cache_key, image_url, self.cache_timeout)
                logger.info(f"✅ Зображення знайдено: {image_url}")
                return image_url
        
        logger.warning("⚠️ Не вдалося знайти підходяще зображення")
        return None
    
    def _build_search_queries(self, title: str, category: str, keywords: List[str] = None) -> List[str]:
        """Створює список пошукових запитів по пріоритету"""
        queries = []
        
        # Маппінг категорій на ключові слова
        category_mapping = {
            'ai': ['artificial intelligence', 'machine learning', 'technology', 'robot'],
            'automation': ['business automation', 'workflow', 'efficiency', 'technology'],
            'crm': ['customer management', 'business', 'sales', 'team'],
            'seo': ['digital marketing', 'analytics', 'growth', 'online'],
            'social': ['social media', 'marketing', 'communication', 'network'],
            'chatbots': ['chatbot', 'ai assistant', 'customer service', 'technology'],
            'ecommerce': ['online shopping', 'ecommerce', 'business', 'retail'],
            'fintech': ['finance', 'banking', 'money', 'technology'],
            'corporate': ['business', 'office', 'corporate', 'professional'],
            'general': ['technology', 'business', 'innovation', 'modern']
        }
        
        # 1. Категорія + основні слова з заголовка
        category_words = category_mapping.get(category, ['technology', 'business'])
        title_words = self._extract_keywords_from_title(title)
        
        if title_words:
            queries.append(f"{category_words[0]} {title_words[0]}")
        
        # 2. Тільки категорія
        queries.append(category_words[0])
        
        # 3. Додаткові ключові слова
        if keywords:
            for keyword in keywords[:2]:  # Тільки перші 2
                queries.append(keyword)
        
        # 4. Фоллбек
        queries.append("business technology")
        
        return queries
    
    def _extract_keywords_from_title(self, title: str) -> List[str]:
        """Витягує ключові слова з заголовка статті"""
        import re
        
        # Стоп-слова які ігноруємо
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Витягуємо слова
        words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
        keywords = [word for word in words if word not in stop_words]
        
        return keywords[:3]  # Повертаємо тільки топ-3
    
    def _try_all_apis(self, query: str) -> Optional[str]:
        """Пробує всі доступні API по черзі"""
        
        # 1. Unsplash (найкраща якість)
        if self.unsplash_key:
            url = self._search_unsplash(query)
            if url:
                return url
        
        # 2. Pexels (більше запитів)
        if self.pexels_key:
            url = self._search_pexels(query)
            if url:
                return url
        
        # 3. Pixabay (найбільша база)
        if self.pixabay_key:
            url = self._search_pixabay(query)
            if url:
                return url
        
        return None
    
    def _search_unsplash(self, query: str) -> Optional[str]:
        """Пошук в Unsplash API"""
        try:
            logger.info(f"🔍 Unsplash пошук: {query}")
            response = self.session.get(
                "https://api.unsplash.com/search/photos",
                headers={"Authorization": f"Client-ID {self.unsplash_key}"},
                params={
                    "query": query,
                    "per_page": 5,
                    "orientation": "landscape",
                    "order_by": "relevant"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    # Беремо перше зображення в середній якості
                    image = data['results'][0]
                    logger.info(f"✅ Unsplash знайшов {len(data['results'])} зображень")
                    return image['urls']['regular']  # 1080px ширина
                else:
                    logger.warning(f"⚠️ Unsplash: немає результатів для '{query}'")
            else:
                logger.error(f"❌ Unsplash API помилка: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"❌ Помилка Unsplash API: {e}")
        
        return None
    
    def _search_pexels(self, query: str) -> Optional[str]:
        """Пошук в Pexels API"""
        try:
            response = self.session.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": self.pexels_key},
                params={
                    "query": query,
                    "per_page": 5,
                    "orientation": "landscape"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['photos']:
                    # Беремо середній розмір
                    photo = data['photos'][0]
                    return photo['src']['large']  # 1880px ширина
                    
        except Exception as e:
            logger.error(f"❌ Помилка Pexels API: {e}")
        
        return None
    
    def _search_pixabay(self, query: str) -> Optional[str]:
        """Пошук в Pixabay API"""
        try:
            response = self.session.get(
                "https://pixabay.com/api/",
                params={
                    "key": self.pixabay_key,
                    "q": query,
                    "image_type": "photo",
                    "orientation": "horizontal",
                    "category": "business",
                    "min_width": 1000,
                    "per_page": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['hits']:
                    # Беремо зображення середньої якості
                    image = data['hits'][0]
                    return image['webformatURL']  # 640px ширина
                    
        except Exception as e:
            logger.error(f"❌ Помилка Pixabay API: {e}")
        
        return None
    
    def _get_cache_key(self, query: str) -> str:
        """Створює ключ для кешування"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
        return f"stock_image:{query_hash}"


# Singleton інстанс для використання в проекті
stock_image_service = StockImageService()

