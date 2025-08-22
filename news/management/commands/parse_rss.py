# === ВИПРАВИТИ news/management/commands/parse_rss.py ===

import time
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from news.services.rss_parser import RSSParser, RSSParserError
from news.models import RSSSource


class Command(BaseCommand):
    help = 'Парсинг RSS джерел новин з опціональними фільтрами'

    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            type=str,
            choices=['en', 'pl', 'uk'],
            help='Фільтр по мові (en, pl, uk)'
        )
        
        parser.add_argument(
            '--category',
            type=str,
            choices=[
                'ai', 'automation', 'crm', 'seo', 'social', 
                'chatbots', 'ecommerce', 'fintech', 'corporate', 'general'
            ],
            help='Фільтр по категорії'
        )
        
        parser.add_argument(
            '--source',
            type=int,
            help='ID конкретного джерела для парсингу'
        )
        
        parser.add_argument(
            '--inactive',
            action='store_true',
            help='Включити неактивні джерела'
        )
        
        parser.add_argument(
            '--cleanup',
            type=int,
            default=0,
            help='Видалити старі статті (днів назад)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Детальний вивід'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            help='Обмежити кількість статей для парсингу (для тестування)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Тестовий запуск без збереження'
        )
        
        # ДОДАЛИ ЦЬОГО АРГУМЕНТА:
        parser.add_argument(
            '--date',
            type=str,
            help='Дата для парсингу в форматі YYYY-MM-DD'
        )
        
        parser.add_argument(
            '--no-date-filter',
            action='store_true',
            help='Вимкнути фільтр по даті'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        # Налаштовуємо вивід
        if options['verbose']:
            self.verbosity = 2
        else:
            self.verbosity = 1
            
        self.stdout.write(
            self.style.SUCCESS('🚀 Початок парсингу RSS джерел')
        )
        
        try:
            # Створюємо парсер
            parser = RSSParser()
            
            # ВИПРАВЛЕНО: Налаштування фільтру по даті
            if options.get('date'):
                try:
                    from datetime import datetime
                    target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                    parser.set_date_filter(target_date)  # ✅ ВИПРАВЛЕНО
                    self.stdout.write(f"📅 Цільова дата: {target_date}")
                except ValueError:
                    raise CommandError('❌ Невірний формат дати. Використовуйте YYYY-MM-DD')
            
            if options.get('no_date_filter'):
                parser.disable_date_filter()  # ✅ ВИПРАВЛЕНО
                self.stdout.write(self.style.WARNING("🚫 Фільтр по даті вимкнений"))
            else:
                if not options.get('date'):
                    # За замовчанням парсимо за вчора
                    from datetime import timedelta
                    yesterday = timezone.now().date() - timedelta(days=1)
                    parser.set_date_filter(yesterday)  # ✅ ВИПРАВЛЕНО
                    self.stdout.write(f"📅 Парсинг новин за: {yesterday}")
            
            # Cleanup старих статей
            if options['cleanup'] > 0:
                self.stdout.write(f"🧹 Очищення статей старше {options['cleanup']} днів...")
                deleted_count = parser.cleanup_old_articles(options['cleanup'])
                self.stdout.write(
                    self.style.WARNING(f"Видалено {deleted_count} старих статей")
                )
            
            # Парсинг конкретного джерела
            if options['source']:
                try:
                    source = RSSSource.objects.get(id=options['source'])
                    self.stdout.write(f"🎯 Парсинг джерела: {source.name}")
                    
                    if options['dry_run']:
                        self.stdout.write(self.style.WARNING("⚠️ DRY RUN - демо режим, дані не зберігаються"))
                        self._demo_parse_source(source)
                        return
                    
                    result = parser.parse_single_source(source)
                    self._print_single_source_results(result, source)
                    
                except RSSSource.DoesNotExist:
                    raise CommandError(f'RSS джерело з ID {options["source"]} не існує')
                    
            else:
                # Парсинг всіх джерел з фільтрами
                active_only = not options['inactive']
                
                if options['dry_run']:
                    self.stdout.write(self.style.WARNING("⚠️ DRY RUN - демо режим"))
                    self._demo_parse_all_sources(
                        language=options['language'],
                        category=options['category'], 
                        active_only=active_only
                    )
                    return
                
                results = parser.parse_all_sources(
                    language=options['language'],
                    category=options['category'],
                    active_only=active_only
                )
                
                self._print_parsing_results(results)
            
            # Час виконання
            execution_time = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f'⏱️ Парсинг завершено за {execution_time:.2f} секунд'
                )
            )
            
        except RSSParserError as e:
            raise CommandError(f'Помилка парсера: {e}')
        except Exception as e:
            raise CommandError(f'Несподівана помилка: {e}')

    def _print_parsing_results(self, results):
        """Виводить результати парсингу всіх джерел"""
        self.stdout.write('\n📊 РЕЗУЛЬТАТИ ПАРСИНГУ:')
        self.stdout.write('-' * 50)
        
        self.stdout.write(f"📚 Всього джерел: {results['total_sources']}")
        self.stdout.write(f"✅ Успішних: {results['successful_sources']}")
        self.stdout.write(f"❌ Помилок: {results['failed_sources']}")
        self.stdout.write(f"📄 Всього статей: {results['total_articles']}")
        self.stdout.write(
            self.style.SUCCESS(f"🆕 Нових статей: {results['new_articles']}")
        )
        self.stdout.write(
            self.style.WARNING(f"🔄 Дублікатів: {results['duplicate_articles']}")
        )
        
        # ✅ ДОДАНО: Показуємо відфільтровані статті
        if 'filtered_articles' in results and results['filtered_articles'] > 0:
            self.stdout.write(
                self.style.WARNING(f"📅 Відфільтровано по даті: {results['filtered_articles']}")
            )
        
        # Помилки
        if results['errors']:
            self.stdout.write('\n❌ ПОМИЛКИ:')
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(error))
        
        # Успішність
        if results['total_sources'] > 0:
            success_rate = (results['successful_sources'] / results['total_sources']) * 100
            if success_rate >= 90:
                style = self.style.SUCCESS
            elif success_rate >= 70:
                style = self.style.WARNING
            else:
                style = self.style.ERROR
                
            self.stdout.write(
                style(f"\n🎯 Успішність: {success_rate:.1f}%")
            )

    def _print_single_source_results(self, result, source):
        """Виводить результати парсингу одного джерела"""
        self.stdout.write(f'\n📊 РЕЗУЛЬТАТИ для {source.name}:')
        self.stdout.write('-' * 50)
        
        self.stdout.write(f"📄 Всього статей: {result['total_articles']}")
        self.stdout.write(
            self.style.SUCCESS(f"🆕 Нових: {result['new_articles']}")
        )
        self.stdout.write(
            self.style.WARNING(f"🔄 Дублікатів: {result['duplicate_articles']}")
        )
        
        if 'filtered_articles' in result:
            self.stdout.write(
                self.style.WARNING(f"⏭️ Відфільтровано: {result['filtered_articles']}")
            )
        
        if result.get('errors', 0) > 0:
            self.stdout.write(
                self.style.ERROR(f"❌ Помилок: {result['errors']}")
            )

    def _demo_parse_all_sources(self, language=None, category=None, active_only=True):
        """Демо режим - показує що буде парситися"""
        
        sources_queryset = RSSSource.objects.all()
        
        if active_only:
            sources_queryset = sources_queryset.filter(is_active=True)
        if language:
            sources_queryset = sources_queryset.filter(language=language)
        if category:
            sources_queryset = sources_queryset.filter(category=category)
        
        sources = list(sources_queryset)
        
        self.stdout.write(f"\n📊 DEMO MODE - Буде оброблено {len(sources)} джерел:")
        self.stdout.write('-' * 60)
        
        for source in sources:
            self.stdout.write(f"🔗 {source.name} ({source.get_language_display()}) - {source.get_category_display()}")
            self.stdout.write(f"    URL: {source.url}")
            
        self.stdout.write(f"\n✅ В реальному режимі ці {len(sources)} джерел будуть парситися!")

    def _demo_parse_source(self, source):
        """Демо режим для одного джерела"""
        self.stdout.write(f"\n📊 DEMO MODE - Джерело: {source.name}")
        self.stdout.write('-' * 50)
        self.stdout.write(f"🌍 Мова: {source.get_language_display()}")
        self.stdout.write(f"📂 Категорія: {source.get_category_display()}")
        self.stdout.write(f"🔗 URL: {source.url}")
        self.stdout.write(f"⚡ Статус: {'Активне' if source.is_active else 'Неактивне'}")
        self.stdout.write(f"🕒 Частота: {source.fetch_frequency} хв")
        self.stdout.write(f"📅 Останнє оновлення: {source.last_fetched or 'Ніколи'}")
        
        self.stdout.write(f"\n✅ В реальному режимі це джерело буде парситися!")