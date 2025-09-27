from django.core.management.base import BaseCommand
from django.utils.translation import activate
from news.models import ProcessedArticle, RawArticle
from news.services.ai_processor.ai_processor_main import AINewsProcessor
import json

class Command(BaseCommand):
    help = 'Тестує генерацію перекладів для статті'

    def add_arguments(self, parser):
        parser.add_argument('--article-id', type=int, help='ID статті для тестування')

    def handle(self, *args, **options):
        article_id = options.get('article_id')
        
        if article_id:
            try:
                article = ProcessedArticle.objects.get(id=article_id)
                raw_article = article.raw_article
            except ProcessedArticle.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Стаття з ID {article_id} не знайдена'))
                return
        else:
            # Беремо останню статтю
            article = ProcessedArticle.objects.first()
            if not article:
                self.stdout.write(self.style.ERROR('Немає оброблених статей'))
                return
            raw_article = article.raw_article

        self.stdout.write(f'Тестуємо статтю: {raw_article.title[:50]}...')
        
        # Показуємо поточні переклади
        self.stdout.write('\n=== ПОТОЧНІ ПЕРЕКЛАДИ ===')
        self.stdout.write(f'Title EN: {article.title_en[:100]}')
        self.stdout.write(f'Title PL: {article.title_pl[:100]}')
        self.stdout.write(f'Title UK: {article.title_uk[:100]}')
        self.stdout.write(f'Summary EN: {article.summary_en[:100]}...')
        self.stdout.write(f'Summary PL: {article.summary_pl[:100]}...')
        self.stdout.write(f'Summary UK: {article.summary_uk[:100]}...')
        
        # Тестуємо генерацію нових перекладів
        self.stdout.write('\n=== ТЕСТУВАННЯ AI ГЕНЕРАЦІЇ ===')
        
        processor = AINewsProcessor()
        
        # Тестуємо _create_multilingual_content
        category_info = {'category': 'general', 'priority': 2}
        content_data = processor._create_multilingual_content(raw_article, category_info)
        
        self.stdout.write('\n=== ЗГЕНЕРОВАНІ ПЕРЕКЛАДИ ===')
        self.stdout.write(f'Title EN: {content_data.get("title_en", "")[:100]}')
        self.stdout.write(f'Title PL: {content_data.get("title_pl", "")[:100]}')
        self.stdout.write(f'Title UK: {content_data.get("title_uk", "")[:100]}')
        self.stdout.write(f'Summary EN: {content_data.get("summary_en", "")[:100]}...')
        self.stdout.write(f'Summary PL: {content_data.get("summary_pl", "")[:100]}...')
        self.stdout.write(f'Summary UK: {content_data.get("summary_uk", "")[:100]}...')
        
        # Перевіряємо, чи переклади різні
        self.stdout.write('\n=== АНАЛІЗ ===')
        if content_data.get("title_pl") == content_data.get("title_en"):
            self.stdout.write(self.style.WARNING('⚠️ Польський заголовок ідентичний англійському'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Польський заголовок відрізняється від англійського'))
            
        if content_data.get("summary_pl") == content_data.get("summary_en"):
            self.stdout.write(self.style.WARNING('⚠️ Польський summary ідентичний англійському'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Польський summary відрізняється від англійського'))
