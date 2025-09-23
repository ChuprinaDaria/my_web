from django.core.management.base import BaseCommand
from django.utils import timezone
from rag.services import IndexingService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Re-indexes all configured RAG content sources from scratch.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting full re-indexing of RAG content..."))
        start_time = timezone.now()

        try:
            indexing_service = IndexingService()
            total_indexed = indexing_service.index_all_content()
            
            # Додатково очистимо застарілі ембеддінги
            self.stdout.write(self.style.WARNING("🧹 Cleaning up orphaned embeddings..."))
            deleted_count = indexing_service.cleanup_orphaned_embeddings()

        except Exception as e:
            logger.error(f"An error occurred during re-indexing: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"❌ An error occurred during re-indexing: {e}"))
            return

        end_time = timezone.now()
        duration = end_time - start_time

        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS(f"✅ Full re-indexing completed successfully!"))
        self.stdout.write(f"⏱️  Duration: {duration}")
        self.stdout.write(f"📄 Total items indexed/updated: {total_indexed}")
        self.stdout.write(f"🗑️  Orphaned embeddings removed: {deleted_count}")
        self.stdout.write(self.style.SUCCESS("=" * 50))
