# rag/management/commands/index_knowledge.py
from django.core.management.base import BaseCommand
from django.conf import settings
from rag.services import IndexingService


class Command(BaseCommand):
    help = 'Індексує весь контент для RAG системи'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reindex',
            action='store_true',
            help='Переіндексувати існуючі записи',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true', 
            help='Видалити застарілі embedding\'и',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Індексувати тільки вказану модель (наприклад: services.ServiceCategory)',
        )

    def handle(self, *args, **options):
        indexing_service = IndexingService()
        
        self.stdout.write('🚀 Починаємо індексацію знань для RAG...')
        
        if options['cleanup']:
            self.stdout.write('🧹 Очищуємо застарілі embedding\'и...')
            deleted = indexing_service.cleanup_orphaned_embeddings()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Видалено {deleted} застарілих записів')
            )
        
        if options['model']:
            # Індексація конкретної моделі
            self.stdout.write(f'📚 Індексуємо модель {options["model"]}...')
            # TODO: Додати логіку для індексації конкретної моделі
        else:
            # Повна індексація
            self.stdout.write('📚 Індексуємо весь контент...')
            total_indexed = indexing_service.index_all_content()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Проіндексовано {total_indexed} записів')
            )
        
        # Виводимо статистику
        from rag.models import EmbeddingModel
        total_embeddings = EmbeddingModel.objects.filter(is_active=True).count()
        languages = EmbeddingModel.objects.values_list('language', flat=True).distinct()
        categories = EmbeddingModel.objects.values_list('content_category', flat=True).distinct()
        
        self.stdout.write('\n📊 Статистика індексації:')
        self.stdout.write(f'   • Загалом embedding\'ів: {total_embeddings}')
        self.stdout.write(f'   • Мови: {", ".join(languages)}')
        self.stdout.write(f'   • Категорії: {", ".join(categories)}')
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Індексація завершена успішно!')
        )