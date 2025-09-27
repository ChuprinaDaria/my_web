from django.core.management.base import BaseCommand
from news.models import RawArticle
from news.services.ai_processor import AINewsProcessor


class Command(BaseCommand):
    help = 'Тестує генерацію контенту для перевірки концепції LAZYSOFT аналізу'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            help='ID конкретної сирої статті для тестування'
        )

    def handle(self, *args, **options):
        article_id = options.get('article_id')
        
        self.stdout.write(
            self.style.SUCCESS('🧪 ТЕСТУВАННЯ КОНЦЕПЦІЇ LAZYSOFT КОНТЕНТУ')
        )
        
        # Отримуємо статтю для тестування
        if article_id:
            try:
                article = RawArticle.objects.get(id=article_id)
            except RawArticle.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Сира стаття з ID {article_id} не знайдена')
                )
                return
        else:
            article = RawArticle.objects.filter(
                is_processed=False,
                is_duplicate=False
            ).first()
        
        if not article:
            self.stdout.write(
                self.style.WARNING('📭 Немає необроблених статей для тестування')
            )
            return
        
        processor = AINewsProcessor()
        
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write('📰 ОРИГІНАЛЬНА СТАТТЯ')
        self.stdout.write(f'{"="*80}')
        
        self.stdout.write(f'Заголовок: {article.title[:100]}...')
        self.stdout.write(f'Джерело: {article.source.name if article.source else "Unknown"}')
        self.stdout.write(f'URL: {article.original_url[:60]}...')
        
        try:
            # Категоризація
            category_info = processor._categorize_article(article)
            
            # Генерація контенту
            self.stdout.write('🤖 Генеруємо LAZYSOFT контент...')
            content = processor._create_multilingual_content(article, category_info)
            
            self.stdout.write(f'\n{"="*80}')
            self.stdout.write('🎯 ЗГЕНЕРОВАНИЙ LAZYSOFT КОНТЕНТ')
            self.stdout.write(f'{"="*80}')
            
            # Заголовок
            self.stdout.write(f'🇺🇦 Заголовок UK: {content.get("title_uk", "N/A")[:80]}...')
            
            # Summary
            summary_uk = content.get('summary_uk', 'N/A')
            self.stdout.write(f'\n📝 SUMMARY UK (перші 800 символів):')
            self.stdout.write('-' * 60)
            self.stdout.write(summary_uk[:800] + ('...' if len(summary_uk) > 800 else ''))
            
            # Business Insight
            insight_uk = content.get('business_insight_uk', 'N/A')
            self.stdout.write(f'\n💡 BUSINESS INSIGHT UK:')
            self.stdout.write('-' * 60)
            self.stdout.write(insight_uk[:300] + ('...' if len(insight_uk) > 300 else ''))
            
            # Перевіряємо концепцію
            self.stdout.write(f'\n{"="*80}')
            self.stdout.write('🔍 АНАЛІЗ КОНЦЕПЦІЇ')
            self.stdout.write(f'{"="*80}')
            
            # Перевіряємо чи є посилання на оригінал
            has_source_link = False
            if article.original_url and article.original_url in summary_uk:
                has_source_link = True
                self.stdout.write('✅ Посилання на оригінал ПРИСУТНЄ')
            else:
                self.stdout.write('❌ Посилання на оригінал ВІДСУТНЄ')
            
            # Перевіряємо чи є згадка джерела
            has_source_mention = False
            if article.source and article.source.name.lower() in summary_uk.lower():
                has_source_mention = True
                self.stdout.write('✅ Згадка джерела ПРИСУТНЯ')
            else:
                self.stdout.write('❌ Згадка джерела ВІДСУТНЯ')
            
            # Перевіряємо чи є LAZYSOFT думки
            lazysoft_patterns = [
                'наші думки', 'наш аналіз', 'наші висновки', 'наша точка зору',
                'команда lazysoft', 'що ми думаємо', 'наші інсайти', 'ділимося'
            ]
            has_lazysoft_opinion = any(pattern in summary_uk.lower() for pattern in lazysoft_patterns)
            
            if has_lazysoft_opinion:
                self.stdout.write('✅ LAZYSOFT думки/аналіз ПРИСУТНІ')
            else:
                self.stdout.write('❌ LAZYSOFT думки/аналіз ВІДСУТНІ')
            
            # Загальна оцінка
            concept_score = sum([has_source_link, has_source_mention, has_lazysoft_opinion])
            
            if concept_score == 3:
                self.stdout.write(self.style.SUCCESS('\n🎉 КОНЦЕПЦІЯ ПОВНІСТЮ ДОТРИМАНА!'))
            elif concept_score >= 2:
                self.stdout.write(self.style.WARNING(f'\n⚠️ КОНЦЕПЦІЯ ЧАСТКОВО ДОТРИМАНА ({concept_score}/3)'))
            else:
                self.stdout.write(self.style.ERROR(f'\n💥 КОНЦЕПЦІЯ НЕ ДОТРИМАНА ({concept_score}/3)'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Помилка тестування: {e}')
            )
        
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(
            self.style.SUCCESS('✅ Тестування завершено!')
        )
