from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import ProcessedArticle
from news.services.ai_processor.ai_processor_main import AINewsProcessor


class Command(BaseCommand):
    help = 'Виправляє пріоритети та топ-статті для існуючих статей'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Кількість статей для обробки (за замовчанням: 50)'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Обробити статті за останні N днів (за замовчанням: 7)'
        )
        
        parser.add_argument(
            '--reset-top',
            action='store_true',
            help='Скинути всі is_top_article перед встановленням нових'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        days = options['days']
        reset_top = options['reset_top']
        
        self.stdout.write(
            self.style.SUCCESS('🔧 ВИПРАВЛЕННЯ ПРІОРИТЕТІВ СТАТЕЙ')
        )
        
        # Отримуємо статті за останні дні
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        
        articles = ProcessedArticle.objects.filter(
            status='published',
            created_at__gte=cutoff_date
        ).order_by('-created_at')[:limit]
        
        if not articles:
            self.stdout.write(
                self.style.WARNING(f'📭 Немає статей за останні {days} днів')
            )
            return
        
        self.stdout.write(f'📄 Знайдено {len(articles)} статей для обробки')
        
        # Скидаємо топ-статті якщо потрібно
        if reset_top:
            ProcessedArticle.objects.filter(
                is_top_article=True,
                created_at__gte=cutoff_date
            ).update(
                is_top_article=False,
                article_rank=None,
                top_selection_date=None
            )
            self.stdout.write('🔄 Скинуто всі топ-статті')
        
        # Використовуємо AI процесор для пріоритизації
        processor = AINewsProcessor()
        processor._auto_prioritize_articles(list(articles))
        
        # Статистика
        top_articles = ProcessedArticle.objects.filter(
            is_top_article=True,
            created_at__gte=cutoff_date
        ).count()
        
        high_priority = ProcessedArticle.objects.filter(
            priority__gte=4,
            created_at__gte=cutoff_date
        ).count()
        
        self.stdout.write('\n📊 РЕЗУЛЬТАТИ:')
        self.stdout.write('=' * 50)
        self.stdout.write(f'🏆 Топ-статей: {top_articles}')
        self.stdout.write(f'⭐ Високий пріоритет (4-5): {high_priority}')
        self.stdout.write(f'📄 Всього оброблено: {len(articles)}')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Виправлення пріоритетів завершено!')
        )
