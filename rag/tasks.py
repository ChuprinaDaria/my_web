from celery import shared_task
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task(name="rag.analyze_conversations_task")
def analyze_conversations_task(days=1, auto_approve=False):
    """
    Analyzes recent chat conversations to find new learning patterns.
    """
    from .learning import ConversationAnalyzer
    
    try:
        analyzer = ConversationAnalyzer()
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Starting conversation analysis from {start_date} to {end_date}...")
        
        new_patterns = analyzer.analyze_sessions(start_date, end_date)
        
        logger.info(f"Found {len(new_patterns)} new potential learning patterns.")
        
        if auto_approve:
            approved_count = 0
            for pattern in new_patterns:
                if analyzer.is_quality_pattern(pattern):
                    pattern.status = 'approved'
                    pattern.save()
                    approved_count += 1
            logger.info(f"Auto-approved {approved_count} high-quality patterns.")

    except Exception as e:
        logger.error(f"Error in analyze_conversations_task: {e}", exc_info=True)

@shared_task(name="rag.cleanup_old_patterns")
def cleanup_old_patterns(days_old=60):
    """
    Deletes old, rejected learning patterns.
    """
    from .models import LearningPattern
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        patterns_to_delete = LearningPattern.objects.filter(
            status='rejected',
            created_at__lt=cutoff_date
        )
        
        count = patterns_to_delete.count()
        if count > 0:
            patterns_to_delete.delete()
            logger.info(f"Successfully deleted {count} old, rejected learning patterns.")
        else:
            logger.info("No old, rejected patterns to delete.")

    except Exception as e:
        logger.error(f"Error in cleanup_old_patterns task: {e}", exc_info=True)
        
@shared_task(name="rag.reindex_approved_patterns")
def reindex_approved_patterns():
    """
    Creates or updates embeddings for approved learning patterns.
    """
    from .models import LearningPattern
    from .services import IndexingService

    try:
        indexing_service = IndexingService()
        patterns_to_index = LearningPattern.objects.filter(status='approved')
        
        indexed_count = 0
        for pattern in patterns_to_index:
            try:
                # Assuming IndexingService has a method to handle pattern objects
                indexing_service.create_embedding_for_object(pattern, language='uk') # or appropriate language
                indexed_count += 1
            except Exception as e:
                logger.error(f"Failed to index learning pattern {pattern.id}: {e}", exc_info=True)

        logger.info(f"Successfully re-indexed {indexed_count} approved learning patterns.")

    except Exception as e:
        logger.error(f"Error in reindex_approved_patterns task: {e}", exc_info=True)
