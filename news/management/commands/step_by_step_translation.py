from django.core.management.base import BaseCommand
from news.models import ProcessedArticle, RawArticle
from news.services.ai_processor.ai_processor_content import AIContentProcessor
import json

class Command(BaseCommand):
    help = 'Покроковий тест перекладів'

    def handle(self, *args, **options):
        article = ProcessedArticle.objects.first()
        if not article:
            self.stdout.write(self.style.ERROR('Немає оброблених статей'))
            return
            
        raw_article = article.raw_article
        self.stdout.write(f'Тестуємо статтю: {raw_article.title[:50]}...')
        
        processor = AIContentProcessor()
        
        # Крок 1: Тільки заголовки
        title_prompt = f"""
        Translate this title to Ukrainian and Polish:
        
        Original: "{raw_article.title}"
        
        Return ONLY valid JSON:
        {{
            "title_en": "{raw_article.title}",
            "title_uk": "Український переклад",
            "title_pl": "Polski przekład"
        }}
        """
        
        try:
            self.stdout.write('\n=== КРОК 1: ЗАГОЛОВКИ ===')
            response = processor._call_ai_model(title_prompt, max_tokens=200)
            
            self.stdout.write(f'Відповідь AI: {response}')
            
            cleaned = processor._clean_json_response(response)
            self.stdout.write(f'Очищено: {cleaned}')
            
            content_data = json.loads(cleaned)
            self.stdout.write(f'✅ Успішно! Поля: {list(content_data.keys())}')
            
            self.stdout.write(f'Title EN: {content_data.get("title_en", "")}')
            self.stdout.write(f'Title PL: {content_data.get("title_pl", "")}')
            self.stdout.write(f'Title UK: {content_data.get("title_uk", "")}')
            
            # Перевіряємо чи переклади різні
            if content_data.get("title_pl") != content_data.get("title_en"):
                self.stdout.write(self.style.SUCCESS('✅ Польський заголовок відрізняється від англійського'))
            else:
                self.stdout.write(self.style.WARNING('⚠️ Польський заголовок ідентичний англійському'))
                
            if content_data.get("title_uk") != content_data.get("title_en"):
                self.stdout.write(self.style.SUCCESS('✅ Український заголовок відрізняється від англійського'))
            else:
                self.stdout.write(self.style.WARNING('⚠️ Український заголовок ідентичний англійському'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка: {e}'))
