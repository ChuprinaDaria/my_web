# news/tasks.py
"""
Celery завдання для автоматичної публікації новин
"""

from celery import shared_task
from django.core.management import call_command
from news.models import ProcessedArticle
import logging

logger = logging.getLogger(__name__)

@shared_task
def publish_article_to_telegram(article_uuid, language='uk'):
    """
    Публікує статтю в Telegram через management команду
    """
    try:
        # Перевіряємо, чи існує стаття
        article = ProcessedArticle.objects.filter(uuid=article_uuid).first()
        if not article:
            logger.error(f"Стаття з UUID {article_uuid} не знайдена")
            return False
        
        # Викликаємо management команду
        call_command('post_telegram', uuid=str(article_uuid), lang=language)
        
        logger.info(f"✅ Стаття {article_uuid} успішно опублікована в Telegram")
        return True
        
    except Exception as e:
        logger.error(f"❌ Помилка публікації статті {article_uuid}: {e}")
        return False

@shared_task
def auto_publish_recent_articles(language='uk', limit=3):
    """
    Автоматично публікує останні статті в Telegram
    """
    try:
        # Отримуємо останні опубліковані статті
        recent_articles = ProcessedArticle.objects.filter(
            status='published'
        ).order_by('-priority', '-published_at')[:limit]
        
        published_count = 0
        for article in recent_articles:
            try:
                # Публікуємо кожну статтю
                success = publish_article_to_telegram.delay(str(article.uuid), language)
                if success:
                    published_count += 1
                    logger.info(f"📢 Завдання публікації створено для статті {article.uuid}")
            except Exception as e:
                logger.error(f"❌ Помилка створення завдання для статті {article.uuid}: {e}")
        
        logger.info(f"✅ Створено {published_count} завдань публікації")
        return published_count
        
    except Exception as e:
        logger.error(f"❌ Помилка автоматичної публікації: {e}")
        return 0
