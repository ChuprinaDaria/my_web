from django.core.management.base import BaseCommand
from news.models import ProcessedArticle, RawArticle
from news.services.smart_news_pipeline import SmartNewsPipeline
from news.services.ai_processor.enhanced_ai_analyzer import EnhancedAIAnalyzer

class Command(BaseCommand):
    help = 'Тестує генерацію Business Impact контенту'

    def add_arguments(self, parser):
        parser.add_argument('--article-id', type=int, help='ID статті для тестування')
        parser.add_argument('--dry-run', action='store_true', help='Тестовий режим')

    def handle(self, *args, **options):
        self.stdout.write("🧪 ТЕСТ ГЕНЕРАЦІЇ BUSINESS IMPACT")
        self.stdout.write("=" * 50)
        
        if options['article_id']:
            try:
                article = ProcessedArticle.objects.get(id=options['article_id'])
                self.stdout.write(f"📄 Тестуємо статтю: {article.title_en}")
                
                # Знаходимо сиру статтю
                raw_article = RawArticle.objects.filter(
                    title__icontains=article.title_en[:50]
                ).first()
                
                if raw_article:
                    self.stdout.write("🔍 Знайдено сиру статтю, тестуємо генерацію...")
                    
                    if not options['dry_run']:
                        # Тестуємо Enhanced AI Analyzer
                        enhanced_analyzer = EnhancedAIAnalyzer()
                        enhanced_insights = enhanced_analyzer.analyze_full_article_with_insights(
                            raw_article, 
                            raw_article.content or raw_article.summary
                        )
                        
                        # Показуємо результати
                        if enhanced_insights.business_insights:
                            en_insights = enhanced_insights.business_insights.get('english_audience', {})
                            uk_insights = enhanced_insights.business_insights.get('ukrainian_audience', {})
                            
                            self.stdout.write(f"\n📊 BUSINESS IMPACT EN ({len(en_insights.get('main_insight', ''))} символів):")
                            self.stdout.write("-" * 50)
                            self.stdout.write(en_insights.get('main_insight', '')[:500] + "...")
                            
                            self.stdout.write(f"\n📊 BUSINESS IMPACT UK ({len(uk_insights.get('main_insight', ''))} символів):")
                            self.stdout.write("-" * 50)
                            self.stdout.write(uk_insights.get('main_insight', '')[:500] + "...")
                            
                            # Тестуємо генерацію повного контенту
                            pipeline = SmartNewsPipeline()
                            full_content_en = pipeline._generate_full_content(
                                raw_article.content or raw_article.summary, 'en'
                            )
                            
                            self.stdout.write(f"\n📝 FULL CONTENT EN ({len(full_content_en)} символів):")
                            self.stdout.write("-" * 50)
                            self.stdout.write(full_content_en[:500] + "...")
                            
                        else:
                            self.stdout.write("❌ Не вдалося створити інсайти")
                    else:
                        self.stdout.write("⚠️ DRY RUN - генерація пропущена")
                else:
                    self.stdout.write("❌ Сиру статтю не знайдено")
                    
            except ProcessedArticle.DoesNotExist:
                self.stdout.write("❌ Статтю не знайдено")
        else:
            self.stdout.write("❌ Вкажіть --article-id")
