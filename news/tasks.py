# news/tasks.py
"""
Celery завдання для автоматичної публікації новин
"""

from celery import shared_task
from .services.rss_parser import RSSParser
from .services.ai_processor.ai_processor_base import AINewsProcessor
from .services.telegram import TelegramService
from .models import RSSSource, ProcessedArticle, SocialMediaPost
from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task(name="news.process_single_article")
def process_single_article_task(article_data, source_id):
    """
    Task to process a single article: AI processing and saving.
    """
    try:
        processor = AINewsProcessor()
        processed_article_instance = processor.process_article(article_data, source_id)
        if processed_article_instance:
            logger.info(f"Article '{processed_article_instance.title_uk}' processed and saved successfully.")
            return processed_article_instance.id
    except Exception as e:
        logger.error(f"Error processing article '{article_data.get('title')}': {e}", exc_info=True)
    return None

@shared_task(name="news.process_rss_source")
def process_rss_source_task(source_id):
    """
    Parses an RSS source and creates individual processing tasks for each new article.
    """
    try:
        source = RSSSource.objects.get(id=source_id, is_active=True)
        parser = RSSParser()
        new_articles = parser.parse_source(source)
        
        logger.info(f"Found {len(new_articles)} new articles from '{source.name}'. Triggering individual processing tasks.")
        
        for article_data in new_articles:
            process_single_article_task.delay(article_data, source_id)
            
        return len(new_articles)
    except RSSSource.DoesNotExist:
        logger.warning(f"RSSSource with id={source_id} not found or not active.")
    except Exception as e:
        logger.error(f"Error processing RSS source id={source_id}: {e}", exc_info=True)
    return 0

@shared_task(name="news.run_all_rss_sources_processing")
def run_all_rss_sources_processing_task():
    """
    Triggers processing for all active RSS sources.
    """
    active_sources = RSSSource.objects.filter(is_active=True)
    logger.info(f"Found {active_sources.count()} active RSS sources to process.")
    for source in active_sources:
        process_rss_source_task.delay(source.id)

@shared_task(name="news.post_top_news_to_telegram")
def post_top_news_to_telegram_task():
    """
    Finds a top unpublished article and posts it to Telegram.
    """
    try:
        # Simple lock to prevent duplicates when multiple triggers fire
        if not cache.add('tg:post_lock', '1', timeout=120):
            logger.info("Telegram post skipped due to lock")
            return

        today = timezone.now().date()
        article_to_post = (ProcessedArticle.objects
            .filter(status='published', is_top_article=True, top_selection_date=today)
            .exclude(social_posts__platform='telegram_uk', social_posts__status='published')
            .order_by('article_rank')
            .first())
        if not article_to_post:
            article_to_post = (ProcessedArticle.objects
                .filter(status='published', priority__gte=3, published_at__date=today)
                .exclude(social_posts__platform='telegram_uk', social_posts__status='published')
                .order_by('-priority', '-published_at')
                .first())

        if not article_to_post:
            logger.info("No new top news to post to Telegram.")
            return

        telegram_service = TelegramService()
        message = (
            f"🔥 *{article_to_post.get_title('uk')}*\n\n"
            f"{article_to_post.get_summary('uk')}\n\n"
            f"🔗 [Читати далі]({article_to_post.get_absolute_url('uk')})"
        )
        
        external_id = telegram_service.post_to_telegram(message, photo_url=article_to_post.ai_image_url)

        smp, _ = SocialMediaPost.objects.get_or_create(
            article=article_to_post,
            platform='telegram_uk',
            defaults={
                'content': message,
                'image_url': article_to_post.ai_image_url,
                'status': 'draft'
            }
        )
        if external_id:
            smp.mark_as_published(external_id)
        
        logger.info(f"Posted article '{article_to_post.get_title('uk')}' to Telegram.")

    except Exception as e:
        logger.error(f"Error in post_top_news_to_telegram_task: {e}", exc_info=True)

@shared_task(name="news.run_full_daily_pipeline")
def run_full_daily_pipeline(date=None, auto_publish=True, skip_rss=False, dry_run=False):
    args = []
    if date:
        args += ["--date", date]
    if auto_publish:
        args += ["--auto-publish"]
    args += ["--full-pipeline"]
    if skip_rss:
        args += ["--skip-rss"]
    if dry_run:
        args += ["--dry-run"]
    call_command("daily_news_pipeline", *args)
