from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import ProcessedArticle, RawArticle
from news.services.ai_processor.enhanced_ai_analyzer import EnhancedAIAnalyzer
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Виправляє оброблені статті: встановлює пріоритет та додає бізнес-інсайти'

    def add_arguments(self, parser):
        parser.add_argument('--article-id', type=int, help='ID обробленої статті для виправлення')
        parser.add_argument('--title-contains', type=str, help='Частина заголовка для пошуку статті')
        parser.add_argument('--priority', type=int, default=4, help='Новий пріоритет (1-5)')
        parser.add_argument('--dry-run', action='store_true', help='Тестовий режим')

    def handle(self, *args, **options):
        self.stdout.write("🔧 FIX PROCESSED ARTICLE")
        self.stdout.write("=" * 50)
        
        # Знаходимо статтю
        article = self._find_article(options)
        if not article:
            self.stdout.write("❌ Статтю не знайдено")
            return
        
        self.stdout.write(f"📄 Знайдено статтю: {article.title_en}")
        self.stdout.write(f"   Поточний пріоритет: {article.priority}")
        self.stdout.write(f"   Бізнес-інсайт EN: {article.business_insight_en[:100] if article.business_insight_en else 'НЕМАЄ'}...")
        
        if options['dry_run']:
            self.stdout.write("⚠️ DRY RUN - зміни не збережено")
            return
        
        # Виправляємо статтю
        try:
            with transaction.atomic():
                # 1. Встановлюємо пріоритет
                article.priority = options['priority']
                article.save(update_fields=['priority'])
                self.stdout.write(f"✅ Пріоритет встановлено: {options['priority']}")
                
                # 2. Додаємо бізнес-інсайти
                if not article.business_insight_en or len(article.business_insight_en.strip()) < 50:
                    self.stdout.write("🤖 Створення бізнес-інсайтів...")
                    
                    # Знаходимо сиру статтю
                    raw_article = RawArticle.objects.filter(
                        title__icontains=article.title_en[:50]
                    ).first()
                    
                    if raw_article:
                        # Використовуємо Enhanced AI Analyzer
                        enhanced_analyzer = EnhancedAIAnalyzer()
                        enhanced_insights = enhanced_analyzer.analyze_full_article_with_insights(
                            raw_article, 
                            raw_article.content or raw_article.summary
                        )
                        
                        # Оновлюємо бізнес-інсайти
                        if enhanced_insights.business_insights:
                            en_insights = enhanced_insights.business_insights.get('english_audience', {})
                            pl_insights = enhanced_insights.business_insights.get('polish_audience', {})
                            uk_insights = enhanced_insights.business_insights.get('ukrainian_audience', {})
                            
                            article.business_insight_en = en_insights.get('main_insight', '')
                            article.business_insight_pl = pl_insights.get('main_insight', '')
                            article.business_insight_uk = uk_insights.get('main_insight', '')
                            
                            # Додаємо ключові моменти
                            if enhanced_insights.key_takeaways:
                                article.key_takeaways_en = enhanced_insights.key_takeaways.get('english', [])
                                article.key_takeaways_pl = enhanced_insights.key_takeaways.get('polish', [])
                                article.key_takeaways_uk = enhanced_insights.key_takeaways.get('ukrainian', [])
                            
                            article.save(update_fields=[
                                'business_insight_en', 'business_insight_pl', 'business_insight_uk',
                                'key_takeaways_en', 'key_takeaways_pl', 'key_takeaways_uk'
                            ])
                            
                            self.stdout.write("✅ Бізнес-інсайти додано")
                        else:
                            self.stdout.write("⚠️ Не вдалося створити бізнес-інсайти")
                    else:
                        self.stdout.write("⚠️ Сиру статтю не знайдено")
                else:
                    self.stdout.write("ℹ️ Бізнес-інсайти вже є")
                
                self.stdout.write(f"🎉 Статтю виправлено успішно!")
                
        except Exception as e:
            self.stdout.write(f"❌ Помилка: {e}")
            logger.error(f"Помилка виправлення статті: {e}")

    def _find_article(self, options):
        """Знаходить статтю за ID або заголовком"""
        if options['article_id']:
            try:
                return ProcessedArticle.objects.get(id=options['article_id'])
            except ProcessedArticle.DoesNotExist:
                return None
        
        if options['title_contains']:
            articles = ProcessedArticle.objects.filter(
                title_en__icontains=options['title_contains']
            )
            if articles.count() == 1:
                return articles.first()
            elif articles.count() > 1:
                self.stdout.write("🔍 Знайдено кілька статей:")
                for i, article in enumerate(articles[:5], 1):
                    self.stdout.write(f"   {i}. ID: {article.id} - {article.title_en[:80]}...")
                return None
        
        return None
