from django.core.management.base import BaseCommand
from news.models import ProcessedArticle, RawArticle
from news.services.ai_processor.ai_processor_content import AIContentProcessor
import json

class Command(BaseCommand):
    help = 'Простий тест перекладів'

    def handle(self, *args, **options):
        article = ProcessedArticle.objects.first()
        if not article:
            self.stdout.write(self.style.ERROR('Немає оброблених статей'))
            return
            
        raw_article = article.raw_article
        self.stdout.write(f'Тестуємо статтю: {raw_article.title[:50]}...')
        
        processor = AIContentProcessor()
        
        # Простий промпт для тестування
        simple_prompt = """
        Translate this title to Ukrainian and Polish:
        
        Original: "What People Do With Workflows"
        
        Return ONLY valid JSON:
        {
            "title_en": "What People Do With Workflows",
            "title_uk": "Що люди роблять з робочими процесами",
            "title_pl": "Co ludzie robią z procesami roboczymi"
        }
        """
        
        try:
            self.stdout.write('\n=== ПРОСТИЙ ТЕСТ ===')
            response = processor._call_ai_model(simple_prompt, max_tokens=500)
            
            self.stdout.write(f'Відповідь AI: {response}')
            
            cleaned = processor._clean_json_response(response)
            self.stdout.write(f'Очищено: {cleaned}')
            
            content_data = json.loads(cleaned)
            self.stdout.write(f'✅ Успішно! Поля: {list(content_data.keys())}')
            
            self.stdout.write(f'Title EN: {content_data.get("title_en", "")}')
            self.stdout.write(f'Title PL: {content_data.get("title_pl", "")}')
            self.stdout.write(f'Title UK: {content_data.get("title_uk", "")}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка: {e}'))
