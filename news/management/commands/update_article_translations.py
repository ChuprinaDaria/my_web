from django.core.management.base import BaseCommand
from news.models import ProcessedArticle
from news.services.ai_processor.ai_processor_content import AIContentProcessor

class Command(BaseCommand):
    help = 'Оновлює переклади заголовків для існуючих статей'

    def add_arguments(self, parser):
        parser.add_argument('--article-id', type=int, help='ID конкретної статті')
        parser.add_argument('--limit', type=int, default=10, help='Кількість статей для оновлення')

    def handle(self, *args, **options):
        article_id = options.get('article_id')
        limit = options.get('limit')

        if article_id:
            articles = ProcessedArticle.objects.filter(id=article_id)
        else:
            # Беремо статті, які мають однакові заголовки (не перекладені)
            articles = []
            all_articles = ProcessedArticle.objects.all()[:limit]

            for article in all_articles:
                # Перевіряємо, чи заголовки ідентичні
                titles_identical = (article.title_en and article.title_pl and article.title_uk and
                    article.title_en.strip() == article.title_pl.strip() and
                    article.title_pl.strip() == article.title_uk.strip())
                
                # Перевіряємо, чи summary ідентичні
                summaries_identical = (article.summary_en and article.summary_pl and article.summary_uk and
                    article.summary_en.strip() == article.summary_pl.strip() and
                    article.summary_pl.strip() == article.summary_uk.strip())
                
                if titles_identical or summaries_identical:
                    articles.append(article)

            articles = articles[:limit]

        processor = AIContentProcessor()
        updated = 0

        for article in articles:
            self.stdout.write(f'Оновлюємо статтю {article.id}: {article.title_uk[:50]}...')

            # Визначаємо оригінальну мову заголовка
            # Спочатку перевіряємо, чи всі заголовки однакові
            titles = [article.title_en, article.title_pl, article.title_uk]
            unique_titles = list(set(t.strip() for t in titles if t and t.strip()))

            if len(unique_titles) <= 1:
                # Всі заголовки однакові або майже однакові - це оригінальна мова
                original_title = article.title_en or article.title_uk or article.title_pl
                original_lang = "English"  # За замовчуванням англійська
            else:
                # Є різні заголовки - знаходимо той, що найбільш схожий на оригінал
                # Зазвичай оригінал - це найдовший або той, що містить більше слів
                original_title = max(unique_titles, key=len)
                original_lang = "English"  # Спростимо - вважатимемо англійською

            if not original_title:
                self.stdout.write(f'  Пропускаємо - немає оригінального заголовка')
                continue

            # Перевіряємо чи потрібно оновити summary
            original_summary = ""
            if (article.summary_en and article.summary_pl and article.summary_uk and
                article.summary_en.strip() == article.summary_pl.strip() and
                article.summary_pl.strip() == article.summary_uk.strip()):
                original_summary = article.summary_en or article.summary_uk or article.summary_pl

            if original_summary:
                prompt = f"""
                Translate this English article title and summary to Ukrainian and Polish.
                Keep the English versions unchanged.

                English title: "{original_title}"
                English summary: "{original_summary[:500]}..."

                Return ONLY valid JSON:
                {{
                    "title_en": "{original_title}",
                    "title_uk": "Ukrainian translation of the title",
                    "title_pl": "Polish translation of the title",
                    "summary_en": "{original_summary}",
                    "summary_uk": "Ukrainian translation of the summary",
                    "summary_pl": "Polish translation of the summary"
                }}

                IMPORTANT: 
                - Keep English versions exactly as provided
                - Provide proper Ukrainian and Polish translations
                - Summary should be concise and informative
                """
            else:
                prompt = f"""
                Translate this English article title to Ukrainian and Polish.
                Keep the English title unchanged.

                English title: "{original_title}"

                Return ONLY valid JSON:
                {{
                    "title_en": "{original_title}",
                    "title_uk": "Ukrainian translation of the title",
                    "title_pl": "Polish translation of the title"
                }}

                IMPORTANT: 
                - title_en must be exactly: "{original_title}"
                - title_uk must be the Ukrainian translation
                - title_pl must be the Polish translation
                """

            try:
                response = processor._call_ai_model(prompt, max_tokens=2000)
                cleaned = processor._clean_json_response(response)

                if cleaned and cleaned != '{}':
                    import json
                    data = json.loads(cleaned)

                    # Оновлюємо заголовки
                    article.title_en = data.get('title_en', article.title_en)
                    article.title_pl = data.get('title_pl', article.title_pl)
                    article.title_uk = data.get('title_uk', article.title_uk)
                    
                    # Оновлюємо summary, якщо є в відповіді
                    if 'summary_en' in data:
                        article.summary_en = data.get('summary_en', article.summary_en)
                        article.summary_pl = data.get('summary_pl', article.summary_pl)
                        article.summary_uk = data.get('summary_uk', article.summary_uk)

                    article.save()

                    self.stdout.write(f'  ✅ Оновлено: EN="{article.title_en[:50]}..."')
                    updated += 1
                else:
                    self.stdout.write(f'  ❌ Помилка парсингу JSON')

            except Exception as e:
                self.stdout.write(f'  ❌ Помилка: {e}')

        self.stdout.write(self.style.SUCCESS(f'Оновлено {updated} статей'))
