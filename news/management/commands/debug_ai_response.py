from django.core.management.base import BaseCommand
from news.models import ProcessedArticle, RawArticle
from news.services.ai_processor.ai_processor_content import AIContentProcessor
import json

class Command(BaseCommand):
    help = 'Детальний дебаг AI відповіді'

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
            article = ProcessedArticle.objects.first()
            if not article:
                self.stdout.write(self.style.ERROR('Немає оброблених статей'))
                return
            raw_article = article.raw_article

        self.stdout.write(f'Тестуємо статтю: {raw_article.title[:50]}...')
        
        processor = AIContentProcessor()
        
        # Тестуємо _create_multilingual_content
        category_info = {'category': 'general', 'priority': 2}
        
        # Створюємо простий промпт для тестування
        original_title = raw_article.title or ""
        full_content = raw_article.content or raw_article.summary or ""
        content_for_ai = full_content[:2000]
        
        test_prompt = f"""
        You are LAZYSOFT's tech/business editor. Create COMPREHENSIVE business analysis 
        based on the FULL ARTICLE CONTENT below for SMB readers in Europe.

        ORIGINAL TITLE: {original_title}
        FULL ARTICLE CONTENT: {content_for_ai}
        CATEGORY: general

        IMPORTANT: You have FULL article content, not just RSS snippet. 
        Use this rich information to create detailed, valuable business insights with SEO-optimized length.

        REQUIREMENTS:
        - Three languages: EN, UK, PL.
        - Each "summary_*" must be 2000–3000 characters for better SEO performance.
        - Extract specific facts, numbers, and actionable insights from the content.
        - You CAN include relevant quotes from the original article (use quotation marks).
        - Focus on business impact for European SMBs with concrete examples.
        - Create comprehensive analysis with multiple paragraphs and detailed explanations.
        - Use the full context to provide deeper insights than typical RSS summaries.
        - Include specific data points, statistics, and concrete business implications.
        - Structure content with clear introduction, main analysis, and actionable conclusions.
        - CRITICAL: Keep each language field completely in its respective language. Do not mix languages within a single field.

        OUTPUT VALID JSON ONLY (no additional text before or after):
        {{
            "title_en": "Business-focused title based on article insights",
            "title_uk": "Бізнес-орієнтований заголовок",
            "title_pl": "Tytuł skoncentrowany na biznesie",
            "summary_en": "Comprehensive analysis using full article content (2000-3000 chars)",
            "summary_uk": "Комплексний аналіз на основі повного контенту (2000-3000 символів)",
            "summary_pl": "Kompleksowa analiza oparta na pełnej treści (2000-3000 znaków)",
            "insight_en": "Specific actionable business insight from article",
            "insight_uk": "Конкретний практичний бізнес-інсайт зі статті",
            "insight_pl": "Konkretny praktyczny biznesowy wgląd z artykułu",
            "business_opportunities_en": "Specific business opportunities for European SMBs (300-500 chars)",
            "business_opportunities_uk": "Конкретні бізнес-можливості для європейських МСП (300-500 символів)",
            "business_opportunities_pl": "Konkretne możliwości biznesowe dla europejskich MŚP (300-500 znaków)",
            "lazysoft_recommendations_en": "LAZYSOFT automation recommendations based on article insights (300-500 chars)",
            "lazysoft_recommendations_uk": "Рекомендації LAZYSOFT з автоматизації на основі інсайтів статті (300-500 символів)",
            "lazysoft_recommendations_pl": "Rekomendacje LAZYSOFT dotyczące automatyzacji na podstawie wglądów z artykułu (300-500 znaków)"
        }}
        """
        
        try:
            self.stdout.write('\n=== ВИКЛИК AI МОДЕЛІ ===')
            response = processor._call_ai_model(test_prompt, max_tokens=4000)
            
            self.stdout.write(f'\n=== ПОВНА ВІДПОВІДЬ AI ===')
            self.stdout.write(f'Довжина: {len(response)} символів')
            self.stdout.write(response)
            
            self.stdout.write(f'\n=== ОЧИЩЕННЯ JSON ===')
            self.stdout.write(f'Початок відповіді: {response[:200]}')
            self.stdout.write(f'Кінець відповіді: {response[-200:]}')
            cleaned = processor._clean_json_response(response)
            self.stdout.write(f'Очищено: {len(cleaned)} символів')
            self.stdout.write(f'Очищений JSON:')
            self.stdout.write(cleaned)
            
            self.stdout.write(f'\n=== ПАРСИНГ JSON ===')
            try:
                content_data = json.loads(cleaned)
                self.stdout.write(f'✅ Успішно розпарсено JSON з {len(content_data)} полями')
                self.stdout.write(f'Поля: {list(content_data.keys())}')
                
                # Показуємо переклади
                self.stdout.write(f'\n=== ПЕРЕКЛАДИ ===')
                self.stdout.write(f'Title EN: {content_data.get("title_en", "")[:100]}')
                self.stdout.write(f'Title PL: {content_data.get("title_pl", "")[:100]}')
                self.stdout.write(f'Title UK: {content_data.get("title_uk", "")[:100]}')
                
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f'❌ Помилка JSON: {e}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка AI: {e}'))