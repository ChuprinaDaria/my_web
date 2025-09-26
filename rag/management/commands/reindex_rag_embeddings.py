from django.core.management.base import BaseCommand
from rag.services import IndexingService
from rag.models import EmbeddingModel
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Переіндексує всі embeddings для RAG системи.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Початок переіндексації RAG embeddings...'))
        
        self.stdout.write(self.style.WARNING('Видалення всіх існуючих embeddings перед переіндексацією...'))
        try:
            deleted_count, _ = EmbeddingModel.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Успішно видалено {deleted_count} старих embeddings.'))
        except Exception as e:
            logger.exception("Помилка під час видалення існуючих embeddings.")
            self.stdout.write(self.style.ERROR(f'Помилка під час видалення старих embeddings: {e}'))
            return # Зупиняємо виконання, якщо видалення не вдалося

        indexing_service = IndexingService()
        try:
            total_indexed = indexing_service.index_all_content()
            self.stdout.write(self.style.SUCCESS(f"Успішно переіндексовано {total_indexed} об'єктів."))
        except Exception as e:
            logger.exception("Помилка під час переіндексації RAG embeddings.")
            self.stdout.write(self.style.ERROR(f"Помилка під час переіндексації: {e}"))
