import time
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from news.models import RawArticle, ProcessedArticle
from news.services.ai_processor import AINewsProcessor
from news.services.ai_processor.ai_processor_database import AIProcessorDatabase


class Command(BaseCommand):
    help = 'AI обробка сирих статей у готові до публікації'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Кількість статей для обробки (за замовчанням: 10)'
        )
        
        parser.add_argument(
            '--category',
            type=str,
            choices=[
                'ai', 'automation', 'crm', 'seo', 'social', 
                'chatbots', 'ecommerce', 'fintech', 'corporate', 'general'
            ],
            help='Обробити тільки статті з певної категорії'
        )
        
        parser.add_argument(
            '--article-id',
            type=int,
            help='ID конкретної статті для обробки'
        )
        
        parser.add_argument(
            '--auto-publish',
            action='store_true',
            help='Автоматично публікувати оброблені статті'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Детальний вивід процесу'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Тестовий запуск (показати що буде оброблено)'
        )
        parser.add_argument('--tg-post', action='store_true', help='Одразу постити в Telegram після паблішу')
        parser.add_argument('--lang', default='uk', help='Мова публікації в ТГ (uk/en/pl)')


    def handle(self, *args, **options):
        start_time = time.time()
        
        self.stdout.write(
            self.style.SUCCESS('🤖 AI ПРОЦЕСОР НОВИН LAZYSOFT')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('⚠️ ТЕСТОВИЙ РЕЖИМ - нічого не обробляється')
            )
            self._show_pending_articles(options)
            return
        
        try:
            # Створюємо AI процесор
            processor = AINewsProcessor()
            
            # Перевіряємо доступність AI
            if not self._check_ai_availability(processor):
                return
            
            # Обробка конкретної статті
            if options['article_id']:
                self._process_single_article(processor, options['article_id'], options)
            else:
                # Пакетна обробка
                self._process_batch(processor, options)
            
            # Час виконання
            execution_time = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f'⏱️ AI обробка завершена за {execution_time:.2f} секунд'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Помилка AI процесора: {e}')
            )

    def _check_ai_availability(self, processor):
        """Перевіряє доступність AI моделей"""
        if not processor.openai_client and not processor.gemini_model:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Жодна AI модель не доступна!\n'
                    'Перевірте налаштування OPENAI_API_KEY або GEMINI_API_KEY в settings.py'
                )
            )
            return False
        
        if processor.openai_client:
            self.stdout.write(' OpenAI доступний')
        if processor.gemini_model:
            self.stdout.write(' Gemini доступний')
            
        return True

    def _show_pending_articles(self, options):
        """Показує статті що будуть оброблені"""
        queryset = RawArticle.objects.filter(
            is_processed=False,
            is_duplicate=False
        ).order_by('-published_at')
        
        if options['category']:
            queryset = queryset.filter(source__category=options['category'])
        
        limit = options.get('limit', 10)
        articles = list(queryset[:limit])
        
        self.stdout.write(f'\n📊 СТАТТІ ДО ОБРОБКИ ({len(articles)}):\n')
        self.stdout.write('=' * 70)
        
        for i, article in enumerate(articles, 1):
            self.stdout.write(
                f'{i:2}. 📰 {article.title[:50]}...\n'
                f'    🏷️  Категорія: {article.source.category}\n'
                f'    📅 Дата: {article.published_at.date()}\n'
                f'    🔗 Джерело: {article.source.name}\n'
            )
        
        if not articles:
            self.stdout.write('📭 Немає статей для обробки')
        else:
            self.stdout.write(f'\n🎯 У реальному режимі буде оброблено {len(articles)} статей')

    def _process_single_article(self, processor, article_id, options):
        """Обробка однієї статті"""
        try:
            article = RawArticle.objects.get(id=article_id)
            
            if article.is_processed:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Стаття вже оброблена: {article.title[:50]}...')
                )
                return
            
            self.stdout.write(f'🤖 Обробка статті: {article.title[:50]}...')
            
            result = processor.process_article(article)
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Стаття успішно оброблена!')
                )
                
                if options['auto_publish']:
                    result.publish()
                    self.stdout.write('📰 Статтю автоматично опубліковано')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Помилка обробки статті')
                )
                
        except RawArticle.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Стаття з ID {article_id} не знайдена')
            )
    def _auto_publish_articles(self):
        """Автоматично публікує готові статті"""
        articles_to_publish = ProcessedArticle.objects.filter(
            status='draft',
            priority__gte=2  # Тільки середній та високий пріоритет
        ).order_by('-priority', '-created_at')[:5]  # Максимум 5 за раз
        
        published_count = 0
        for article in articles_to_publish:
            try:
                article.publish()
                published_count += 1
                self.stdout.write(f'📰 Опубліковано: {article.title_uk[:50]}...')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Помилка публікації: {e}')
                )

    def _process_batch(self, processor, options):
        """Пакетна обробка статей"""
        limit = options.get('limit', 10)
        category = options.get('category')
        
        self.stdout.write(f'🚀 Пакетна обробка: до {limit} статей')
        if category:
            self.stdout.write(f'📂 Категорія: {category}')
        
        # Запускаємо обробку
        results = processor.process_batch(limit=limit, category=category)
        
        # Показуємо результати
        self.stdout.write('\n📊 РЕЗУЛЬТАТИ AI ОБРОБКИ:')
        self.stdout.write('=' * 50)
        self.stdout.write(f'📄 Оброблено статей: {results["processed"]}')
        self.stdout.write(f'✅ Успішних: {results["successful"]}')
        self.stdout.write(f'❌ Помилок: {results["failed"]}')
        self.stdout.write(f'💰 Загальна вартість: ${results["total_cost"]:.4f}')
        self.stdout.write(f'⏱️ Час обробки: {results["total_time"]:.2f}с')
        
        # Автопублікація
        if options['auto_publish'] and results['successful'] > 0:
            published_count = self._auto_publish_articles()
            self.stdout.write(
                self.style.SUCCESS(f'📰 Автоматично опубліковано: {published_count} статей')
            )
        
        # Статистика загальна
        total_pending = RawArticle.objects.filter(is_processed=False, is_duplicate=False).count()
        total_ready = ProcessedArticle.objects.filter(status='draft').count()
        
        self.stdout.write(f'\n📈 ЗАГАЛЬНА СТАТИСТИКА:')
        self.stdout.write(f'⏳ Залишилось для обробки: {total_pending}')
        self.stdout.write(f'📋 Готових до публікації: {total_ready}')

    
    
        
        return published_count