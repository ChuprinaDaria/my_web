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
            '--dry-run',
            action='store_true',
            help='Тестовий запуск без збереження'
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
                        self.stdout.write(self.style.WARNING("⚠️ DRY RUN - нічого не зберігається"))
                        return
                    
                    result = parser.parse_single_source(source)
                    self._print_single_source_results(result, source)
                    
                except RSSSource.DoesNotExist:
                    raise CommandError(f'RSS джерело з ID {options["source"]} не існує')
                    
            else:
                # Парсинг всіх джерел з фільтрами
                active_only = not options['inactive']
                
                if options['dry_run']:
                    self.stdout.write(self.style.WARNING("⚠️ DRY RUN - нічого не зберігається"))
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
        
        if result.get('errors', 0) > 0:
            self.stdout.write(
                self.style.ERROR(f"❌ Помилок: {result['errors']}")
            )