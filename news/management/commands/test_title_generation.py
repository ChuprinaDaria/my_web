from django.core.management.base import BaseCommand
from news.models import RawArticle
from news.services.ai_processor import AINewsProcessor


class Command(BaseCommand):
    help = 'Тестує генерацію заголовків для перевірки унікальності'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            help='ID конкретної сирої статті для тестування'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=3,
            help='Кількість статей для тестування (за замовчанням: 3)'
        )

    def handle(self, *args, **options):
        article_id = options.get('article_id')
        limit = options.get('limit')
        
        self.stdout.write(
            self.style.SUCCESS('🧪 ТЕСТУВАННЯ ГЕНЕРАЦІЇ ЗАГОЛОВКІВ')
        )
        
        # Отримуємо статті для тестування
        if article_id:
            try:
                articles = [RawArticle.objects.get(id=article_id)]
            except RawArticle.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Сира стаття з ID {article_id} не знайдена')
                )
                return
        else:
            articles = RawArticle.objects.filter(
                is_processed=False,
                is_duplicate=False
            ).order_by('-published_at')[:limit]
        
        if not articles:
            self.stdout.write(
                self.style.WARNING('📭 Немає необроблених статей для тестування')
            )
            return
        
        processor = AINewsProcessor()
        
        for i, article in enumerate(articles, 1):
            self.stdout.write(f'\n{"="*80}')
            self.stdout.write(f'🧪 ТЕСТ {i}/{len(articles)}')
            self.stdout.write(f'{"="*80}')
            
            self.stdout.write(f'📰 Оригінальний заголовок:')
            self.stdout.write(f'   {article.title[:100]}...')
            
            self.stdout.write(f'🏷️  Джерело: {article.source.name if article.source else "Unknown"}')
            self.stdout.write(f'🔗 URL: {article.original_url[:60]}...')
            
            try:
                # Категоризація
                category_info = processor._categorize_article(article)
                self.stdout.write(f'📂 Категорія: {category_info["category"]}')
                
                # Генерація контенту
                self.stdout.write('🤖 Генеруємо контент...')
                content = processor._create_multilingual_content(article, category_info)
                
                self.stdout.write('\n🎯 ЗГЕНЕРОВАНІ ЗАГОЛОВКИ:')
                self.stdout.write('-' * 60)
                
                # Перевіряємо унікальність
                original_clean = article.title.strip().lower()
                
                for lang in ['en', 'uk', 'pl']:
                    title_key = f'title_{lang}'
                    generated_title = content.get(title_key, 'N/A')
                    
                    # Перевіряємо чи унікальний
                    is_unique = generated_title.strip().lower() != original_clean
                    status = '✅ УНІКАЛЬНИЙ' if is_unique else '❌ ІДЕНТИЧНИЙ'
                    
                    lang_flag = {'en': '🇬🇧', 'uk': '🇺🇦', 'pl': '🇵🇱'}[lang]
                    
                    self.stdout.write(f'{lang_flag} {lang.upper()}: {generated_title[:80]}...')
                    self.stdout.write(f'   {status}')
                
                # Загальна оцінка
                titles = [content.get(f'title_{lang}', '') for lang in ['en', 'uk', 'pl']]
                unique_count = sum(1 for title in titles if title.strip().lower() != original_clean)
                
                if unique_count == 3:
                    self.stdout.write(self.style.SUCCESS('\n🎉 ВСІ ЗАГОЛОВКИ УНІКАЛЬНІ!'))
                elif unique_count > 0:
                    self.stdout.write(self.style.WARNING(f'\n⚠️ {unique_count}/3 заголовків унікальні'))
                else:
                    self.stdout.write(self.style.ERROR('\n💥 ВСІ ЗАГОЛОВКИ ІДЕНТИЧНІ ОРИГІНАЛУ!'))
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Помилка тестування: {e}')
                )
        
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(
            self.style.SUCCESS('✅ Тестування завершено!')
        )
