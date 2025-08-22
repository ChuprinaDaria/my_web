from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from news.services.smart_news_pipeline import SmartNewsPipeline

class Command(BaseCommand):
    help = 'Запускає Smart News Pipeline для автоматичної обробки новин'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Дата для обробки у форматі YYYY-MM-DD (за замовчанням сьогодні)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Тестовий режим без збереження в базу даних'
        )
        parser.add_argument(
            '--full-pipeline',
            action='store_true',
            help='Запустити повний пайплайн (селекція + обробка + публікація)'
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Перевірити здоров\'я всіх компонентів пайплайна'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Показати статистику роботи пайплайна'
        )

    def handle(self, *args, **options):
        
        # Ініціалізуємо пайплайн
        pipeline = SmartNewsPipeline()
        
        # Health check
        if options['health_check']:
            self.stdout.write(
                self.style.SUCCESS('🔍 Перевірка здоров\'я компонентів...')
            )
            
            health = pipeline.health_check()
            
            if health.get('overall', False):
                self.stdout.write(
                    self.style.SUCCESS('✅ Всі компоненти працюють коректно!')
                )
                for component, status in health.items():
                    if component != 'overall':
                        icon = '✅' if status else '❌'
                        self.stdout.write(f'   {icon} {component}: {"OK" if status else "FAIL"}')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Виявлені проблеми з компонентами!')
                )
                if 'error' in health:
                    self.stdout.write(f'   Помилка: {health["error"]}')
            
            return
        
        # Статистика
        if options['stats']:
            self.stdout.write(
                self.style.SUCCESS('📊 Статистика Smart News Pipeline:')
            )
            
            stats = pipeline.get_pipeline_statistics()
            
            self.stdout.write(f'🔄 Всього запусків: {stats["total_runs"]}')
            self.stdout.write(f'✅ Успішних: {stats["successful_runs"]}')
            self.stdout.write(f'📄 Статей оброблено: {stats["total_articles_processed"]}')
            self.stdout.write(f'⏰ Середній час: {stats["avg_processing_time"]:.1f}с')
            
            # Статистика компонентів
            components = stats.get('components', {})
            if components:
                self.stdout.write('\n📦 Статистика компонентів:')
                
                # Full Parser
                parser_stats = components.get('full_parser', {})
                if parser_stats:
                    self.stdout.write(f'   📄 Full Parser: {parser_stats.get("success_rate_percent", 0):.1f}% успішність')
                
                # AI Processor
                ai_stats = components.get('ai_processor', {})
                if ai_stats:
                    self.stdout.write(f'   🤖 AI Processor: ${ai_stats.get("total_cost", 0):.4f} загальна вартість')
            
            return
        
        # Парсинг дати
        target_date = None
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Невірний формат дати. Використовуйте YYYY-MM-DD')
        else:
            target_date = timezone.now().date()
        
        # Режими роботи
        dry_run = options['dry_run']
        full_pipeline = options['full_pipeline']
        
        mode_text = "🧪 ТЕСТОВИЙ РЕЖИМ" if dry_run else "🚀 РОБОЧИЙ РЕЖИМ"
        pipeline_text = "ПОВНИЙ ПАЙПЛАЙН" if full_pipeline else "БАЗОВА ОБРОБКА"
        
        self.stdout.write(
            self.style.SUCCESS(f'{mode_text} - {pipeline_text}')
        )
        self.stdout.write(f'📅 Дата обробки: {target_date}')
        self.stdout.write('-' * 60)
        
        # Запускаємо пайплайн
        try:
            if full_pipeline:
                # Повний пайплайн
                self.stdout.write('🚀 Запуск повного Smart News Pipeline...')
                result = pipeline.run_daily_pipeline(date=target_date, dry_run=dry_run)
                
                # Результати
                self.stdout.write('\n📊 РЕЗУЛЬТАТИ:')
                self.stdout.write(f'⏰ Час обробки: {result.processing_time:.1f} секунд')
                self.stdout.write(f'📄 Статей проаналізовано: {result.total_articles_processed}')
                self.stdout.write(f'🎯 Топ статей вибрано: {result.top_articles_selected}')
                self.stdout.write(f'📢 Статей опубліковано: {result.articles_published}')
                self.stdout.write(f'📰 Дайджест створено: {"✅" if result.digest_created else "❌"}')
                self.stdout.write(f'💰 ROI розраховано: {"✅" if result.roi_calculated else "❌"}')
                self.stdout.write(f'📈 Успішність: {result.success_rate:.1f}%')
                
                if result.errors:
                    self.stdout.write('\n⚠️ ПОМИЛКИ:')
                    for error in result.errors:
                        self.stdout.write(f'   ❌ {error}')
                
                if result.success_rate >= 80:
                    self.stdout.write(
                        self.style.SUCCESS('\n🎉 Пайплайн виконано успішно!')
                    )
                elif result.success_rate >= 50:
                    self.stdout.write(
                        self.style.WARNING('\n⚠️ Пайплайн виконано з попередженнями')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('\n❌ Пайплайн виконано з помилками')
                    )
            
            else:
                # Базова обробка (тільки селекція топ статей)
                self.stdout.write('🎯 Запуск селекції топ статей...')
                
                top_articles = pipeline.audience_analyzer.get_daily_top_articles(
                    date=target_date, limit=5
                )
                
                if top_articles:
                    self.stdout.write(f'\n✅ Знайдено {len(top_articles)} топ статей:')
                    
                    for i, (article, analysis) in enumerate(top_articles, 1):
                        self.stdout.write(
                            f'   {i}. [{analysis.relevance_score}/10] {article.title[:60]}...'
                        )
                        self.stdout.write(
                            f'      💼 {analysis.business_impact} вплив | 💰 {analysis.cost_implications}'
                        )
                    
                    if not dry_run:
                        self.stdout.write(
                            '\n💡 Для повної обробки використовуйте --full-pipeline'
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️ Не знайдено статей для обробки')
                    )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Критична помилка: {str(e)}')
            )
            raise CommandError(f'Пайплайн завершився з помилкою: {str(e)}')
        
        self.stdout.write('\n✅ Команда завершена!')