# news/management/commands/daily_news_pipeline.py
import time
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.utils import timezone
from datetime import datetime, timedelta
from news.services.smart_news_pipeline import SmartNewsPipeline
from news.models import RawArticle, ProcessedArticle

class Command(BaseCommand):
    help = 'Запускає повний Smart News Pipeline для щоденної обробки новин'

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
            '--force-reprocess',
            action='store_true',
            help='Переобробити вже оброблені статті'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Максимальна кількість топ статей для обробки (за замовчанням 5)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Детальний вивід процесу'
        )
        parser.add_argument(
            '--skip-rss',
            action='store_true',
            help='Пропустити парсинг RSS (використовувати існуючі статті)'
        )
        parser.add_argument(
            '--auto-publish',
            action='store_true',
            help='Автоматично публікувати топ статті'
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Перевірити здоров\'я всіх компонентів пайплайна'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        # Налаштування логування
        if options['verbose']:
            import logging
            logging.getLogger('news.services').setLevel(logging.INFO)
        
        # Health check
        if options['health_check']:
            self._run_health_check()
            return
        
        # Парсинг дати
        target_date = self._parse_date(options.get('date'))
        
        # Режими роботи
        dry_run = options['dry_run']
        full_pipeline = options['full_pipeline']
        
        # Заголовок
        mode_text = "🧪 ТЕСТОВИЙ РЕЖИМ" if dry_run else "🚀 РОБОЧИЙ РЕЖИМ"
        pipeline_text = "ПОВНИЙ ПАЙПЛАЙН" if full_pipeline else "БАЗОВА ОБРОБКА"
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 LAZYSOFT Smart News Pipeline')
        )
        self.stdout.write(f'{mode_text} | {pipeline_text} | 📅 {target_date}')
        self.stdout.write('=' * 70)
        
        # Показуємо статистику ПЕРЕД обробкою
        self._show_pre_pipeline_stats(target_date)
        
        try:
            # Ініціалізуємо пайплайн
            pipeline = SmartNewsPipeline()
            
            # Крок 0: Парсинг RSS (якщо не пропускаємо)
            if not options['skip_rss']:
                self._run_rss_parsing(target_date, dry_run)
            
            if full_pipeline:
                # Повний пайплайн
                self.stdout.write('\n🔄 Запуск повного Smart News Pipeline...')
                result = pipeline.run_daily_pipeline(
                    date=target_date, 
                    dry_run=dry_run
                )
                
                # Автопублікація
                if options['auto_publish'] and not dry_run:
                    self._auto_publish_articles(result)
                
                # Результати повного пайплайна
                self._show_full_pipeline_results(result)
                
            else:
                # Базова обробка - тільки селекція топ статей
                self._run_basic_processing(pipeline, target_date, options)
            
            # Показуємо статистику ПІСЛЯ обробки
            self._show_post_pipeline_stats(target_date)
            
            # Загальний час виконання
            execution_time = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(f'\n⏱️ Pipeline завершено за {execution_time:.1f} секунд')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Критична помилка: {str(e)}')
            )
            raise CommandError(f'Pipeline завершився з помилкою: {str(e)}')

    def _parse_date(self, date_str):
        """Парсить дату або використовує сьогодні"""
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Невірний формат дати. Використовуйте YYYY-MM-DD')
        return timezone.now().date()

    def _run_health_check(self):
        """Перевіряє здоров'я всіх компонентів"""
        self.stdout.write(
            self.style.SUCCESS('🔍 Перевірка здоров\'я Smart News Pipeline...')
        )
        
        try:
            pipeline = SmartNewsPipeline()
            health = pipeline.health_check()
            
            self.stdout.write('\n📊 СТАН КОМПОНЕНТІВ:')
            self.stdout.write('-' * 50)
            
            components = [
                ('🤖 AI Processor', health.get('ai_processor', False)),
                ('🎯 Audience Analyzer', health.get('audience_analyzer', False)),
                ('📄 Full Parser', health.get('full_parser', False)),
            ]
            
            for name, status in components:
                icon = '✅' if status else '❌'
                status_text = 'OK' if status else 'FAIL'
                style = self.style.SUCCESS if status else self.style.ERROR
                self.stdout.write(style(f'   {icon} {name}: {status_text}'))
            
            # Загальний статус
            overall = health.get('overall', False)
            if overall:
                self.stdout.write(
                    self.style.SUCCESS('\n🎉 Всі компоненти працюють коректно!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('\n⚠️ Виявлені проблеми з компонентами!')
                )
                if 'error' in health:
                    self.stdout.write(f'   Деталі: {health["error"]}')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Помилка health check: {e}')
            )

    def _show_pre_pipeline_stats(self, date):
        """Показує статистику перед запуском пайплайна"""
        # Статті за дату
        raw_today = RawArticle.objects.filter(fetched_at__date=date)
        processed_today = ProcessedArticle.objects.filter(created_at__date=date)
        
        # Загальна статистика
        total_raw = RawArticle.objects.count()
        total_processed = ProcessedArticle.objects.count()
        pending = RawArticle.objects.filter(is_processed=False, is_duplicate=False).count()
        
        self.stdout.write(f'\n📊 ПОТОЧНА СТАТИСТИКА:')
        self.stdout.write('-' * 40)
        self.stdout.write(f'📅 За {date}:')
        self.stdout.write(f'   📰 Сирих статей: {raw_today.count()}')
        self.stdout.write(f'    Оброблених: {processed_today.count()}')
        self.stdout.write(f'\n📈 Загальна база:')
        self.stdout.write(f'   📚 Всього сирих: {total_raw:,}')
        self.stdout.write(f'   🎨 Всього оброблених: {total_processed:,}')
        self.stdout.write(f'   ⏳ Очікують обробки: {pending:,}')

    def _run_rss_parsing(self, date, dry_run):
        """Запускає парсинг RSS за дату"""
        self.stdout.write('\n📡 Крок 0: Парсинг RSS джерел...')
        
        try:
            from io import StringIO
            
            # Перехоплюємо вивід RSS команди
            out = StringIO()
            call_command(
                'parse_rss',
                date=date.strftime('%Y-%m-%d'),
                verbose=True,
                stdout=out
            )
            
            # Показуємо результат
            output = out.getvalue()
            if '🆕 Нових статей:' in output:
                # Витягуємо кількість нових статей
                for line in output.split('\n'):
                    if '🆕 Нових статей:' in line:
                        self.stdout.write(f'   {line.strip()}')
                        break
            else:
                self.stdout.write('   📡 RSS парсинг завершено')
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Помилка RSS парсингу: {e}')
            )

    def _run_basic_processing(self, pipeline, date, options):
        """Запускає базову обробку - тільки селекція топ статей"""
        self.stdout.write('\n🎯 Базова обробка: Селекція топ статей...')
        
        try:
            limit = options['limit']
            top_articles = pipeline.audience_analyzer.get_daily_top_articles(
                date=date, 
                limit=limit
            )
            
            if top_articles:
                self.stdout.write(f'\n✅ Знайдено {len(top_articles)} топ статей:')
                self.stdout.write('-' * 60)
                
                for i, (article, analysis) in enumerate(top_articles, 1):
                    # Індикатор якості
                    score_color = self.style.SUCCESS if analysis.relevance_score >= 8 else \
                                  self.style.WARNING if analysis.relevance_score >= 6 else \
                                  self.style.ERROR
                    
                    self.stdout.write(
                        f'   {i}. {score_color(f"[{analysis.relevance_score}/10]")} '
                        f'{article.title[:55]}...'
                    )
                    self.stdout.write(
                        f'      💼 {analysis.business_impact} вплив | '
                        f'💰 {analysis.cost_implications} | '
                        f'🎯 {analysis.target_audience}'
                    )
                
                self.stdout.write(
                    f'\n💡 Для повної обробки використовуйте --full-pipeline'
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Не знайдено статей для обробки')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Помилка базової обробки: {e}')
            )

    def _show_full_pipeline_results(self, result):
        """Показує результати повного пайплайна"""
        self.stdout.write('\n📊 РЕЗУЛЬТАТИ ПОВНОГО ПАЙПЛАЙНА:')
        self.stdout.write('=' * 50)
        
        # Основні метрики
        self.stdout.write(f'📄 Статей проаналізовано: {result.total_articles_processed}')
        self.stdout.write(f'🎯 Топ статей вибрано: {result.top_articles_selected}')
        self.stdout.write(f'📢 Статей опубліковано: {result.articles_published}')
        self.stdout.write(f'📰 Дайджест створено: {"✅" if result.digest_created else "❌"}')
        self.stdout.write(f'💰 ROI розраховано: {"✅" if result.roi_calculated else "❌"}')
        
        # Успішність
        success_rate = result.success_rate
        if success_rate >= 80:
            style = self.style.SUCCESS
            icon = '🎉'
        elif success_rate >= 50:
            style = self.style.WARNING
            icon = '⚠️'
        else:
            style = self.style.ERROR
            icon = '❌'
        
        self.stdout.write(style(f'\n{icon} Успішність: {success_rate:.1f}%'))
        
        # Помилки
        if result.errors:
            self.stdout.write('\n⚠️ ПОМИЛКИ:')
            for i, error in enumerate(result.errors, 1):
                self.stdout.write(f'   {i}. {error}')

    def _auto_publish_articles(self, result):
        """Автоматично публікує оброблені статті"""
        if result.articles_published > 0:
            self.stdout.write(f'\n📢 Автопублікація {result.articles_published} статей...')
            
            # Автоматична публікація в Telegram через Celery
            try:
                from news.tasks import auto_publish_recent_articles
                
                # Створюємо завдання для публікації
                task = auto_publish_recent_articles.delay('uk', 3)
                self.stdout.write(f'   📢 Створено Celery завдання: {task.id}')
                self.stdout.write(f'   ✅ Завдання публікації в Telegram поставлено в чергу')
                
            except Exception as e:
                self.stdout.write(f'   ❌ Помилка створення завдання публікації: {e}')
                
                # Fallback - пряма публікація
                try:
                    recent_articles = ProcessedArticle.objects.filter(
                        status='published',
                        published_at__date=result.date
                    ).order_by('-priority', '-published_at')[:3]
                    
                    posted_count = 0
                    for article in recent_articles:
                        try:
                            call_command('post_telegram', uuid=str(article.uuid), lang='uk')
                            posted_count += 1
                        except Exception as e:
                            self.stdout.write(f'   ⚠️ Помилка постингу: {e}')
                    
                    self.stdout.write(f'   ✅ Опубліковано в Telegram (fallback): {posted_count} статей')
                    
                except Exception as e:
                    self.stdout.write(f'   ❌ Помилка fallback публікації: {e}')

    def _show_post_pipeline_stats(self, date):
        """Показує статистику після пайплайна"""
        # Оновлена статистика
        processed_today = ProcessedArticle.objects.filter(created_at__date=date)
        published_today = ProcessedArticle.objects.filter(
            published_at__date=date,
            status='published'
        )
        pending = RawArticle.objects.filter(is_processed=False, is_duplicate=False).count()
        
        self.stdout.write(f'\n📈 ФІНАЛЬНА СТАТИСТИКА:')
        self.stdout.write('-' * 40)
        self.stdout.write(f'📅 За {date}:')
        self.stdout.write(f'   🎨 Оброблено: {processed_today.count()}')
        self.stdout.write(f'   📢 Опубліковано: {published_today.count()}')
        self.stdout.write(f'   ⏳ Залишилось: {pending:,}')
        
        # Топ категорії за день
        if processed_today.exists():
            from django.db.models import Count
            top_categories = processed_today.values(
                'category__name_uk', 'category__icon'
            ).annotate(count=Count('id')).order_by('-count')[:3]
            
            if top_categories:
                self.stdout.write(f'\n🏆 Топ категорії:')
                for cat in top_categories:
                    icon = cat['category__icon'] or '📄'
                    name = cat['category__name_uk'] or 'Невідома'
                    count = cat['count']
                    self.stdout.write(f'   {icon} {name}: {count} статей')