from django.core.management.base import BaseCommand
from django.utils import timezone
from typing import List
from news.services.rss_parser import RSSParser
from news.services.smart_article_selector import SmartArticleSelector
from news.services.ai_processor import AINewsProcessor
from news.models import RawArticle

class Command(BaseCommand):
    help = 'Розширений пайплайн: RSS → Smart Selection → FiveFilters → AI → Publish'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=10, help='Кількість статей для обробки')
        parser.add_argument('--category', type=str, help='Категорія для фільтрації')
        parser.add_argument('--dry-run', action='store_true', help='Тестовий режим')
        parser.add_argument('--verbose', action='store_true', help='Детальний вивід')
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 ENHANCED NEWS PIPELINE")
        self.stdout.write("=" * 50)
        
        # 1. Smart Selection
        self.stdout.write("📊 Крок 1: Smart Selection...")
        selector = SmartArticleSelector()
        selected_articles = selector.select_top_articles(
            limit=options['limit'],
            category=options.get('category')
        )
        
        if not selected_articles:
            self.stdout.write("❌ Немає статей для обробки")
            return
        
        self.stdout.write(f"✅ Вибрано {len(selected_articles)} статей")
        
        # 2. FiveFilters Enhancement
        self.stdout.write("\n🔍 Крок 2: FiveFilters Enhancement...")
        enhanced_count = self._enhance_articles_with_fulltext(selected_articles, options['dry_run'])
        
        # 3. AI Processing
        self.stdout.write(f"\n🤖 Крок 3: AI Processing...")
        if not options['dry_run']:
            processed_count = self._process_articles_with_ai(selected_articles)
            self.stdout.write(f"✅ AI обробив {processed_count} статей")
        else:
            self.stdout.write("⚠️ DRY RUN - AI обробка пропущена")
        
        self.stdout.write(f"\n🎉 Pipeline завершено!")
    
    def _enhance_articles_with_fulltext(self, articles: List[RawArticle], dry_run: bool) -> int:
        """Збагачує статті повним текстом"""
        from news.services.fulltext_extractor import FullTextExtractor
        
        if dry_run:
            self.stdout.write("⚠️ DRY RUN - FiveFilters пропущено")
            return 0
        
        extractor = FullTextExtractor()
        enhanced_count = 0
        
        for i, article in enumerate(articles, 1):
            self.stdout.write(f"[{i}/{len(articles)}] {article.title[:50]}...")
            
            try:
                full_content = extractor.extract_article(article.original_url)
                
                if full_content and len(full_content) > len(article.content or ""):
                    original_length = len(article.content or "")
                    article.content = full_content
                    article.save()
                    
                    improvement = len(full_content) - original_length
                    self.stdout.write(f"  ✅ +{improvement} символів")
                    enhanced_count += 1
                else:
                    self.stdout.write(f"  ⚠️ RSS контент кращий")
                    
            except Exception as e:
                self.stdout.write(f"  ❌ Помилка: {e}")
        
        return enhanced_count
    
    def _process_articles_with_ai(self, articles: List[RawArticle]) -> int:
        """Обробляє статті через AI"""
        processor = AINewsProcessor()
        processed_count = 0
        
        for article in articles:
            try:
                result = processor.process_article(article)
                if result:
                    processed_count += 1
                    article.is_processed = True
                    article.save()
            except Exception as e:
                self.stdout.write(f"❌ AI помилка для {article.title[:30]}: {e}")
        
        return processed_count