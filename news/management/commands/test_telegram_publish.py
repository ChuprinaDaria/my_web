from django.core.management.base import BaseCommand
from news.models import ProcessedArticle
from news.services.telegram import TelegramService

class Command(BaseCommand):
    help = 'Тестує публікацію статті в Telegram'

    def add_arguments(self, parser):
        parser.add_argument('--article-id', type=int, help='ID статті для публікації')
        parser.add_argument('--dry-run', action='store_true', help='Тестовий режим')

    def handle(self, *args, **options):
        self.stdout.write("📱 ТЕСТ ПУБЛІКАЦІЇ В TELEGRAM")
        self.stdout.write("=" * 50)
        
        if options['article_id']:
            try:
                article = ProcessedArticle.objects.get(id=options['article_id'])
                self.stdout.write(f"📄 Стаття: {article.get_title('uk')}")
                
                # Формуємо повідомлення з українським контентом
                # Якщо title_uk такий же як title_en (англійський), використовуємо business_insight_uk для заголовка
                if article.title_uk == article.title_en and article.business_insight_uk:
                    title = article.business_insight_uk[:80] + "..."
                else:
                    title = article.title_uk[:80] if article.title_uk else article.title_en[:80]
                
                # Summary - якщо український summary порожній або такий же як англійський, використовуємо business_insight_uk
                if article.summary_uk and article.summary_uk != article.summary_en:
                    summary = article.summary_uk[:200]
                elif article.business_insight_uk:
                    summary = article.business_insight_uk[:200] + "..."
                else:
                    summary = article.summary_en[:200]
                
                message = (
                    f"🔥 <strong>{title}</strong>\n\n"
                    f"{summary}\n\n"
                    f"— <em>Lazysoft AI News</em>"
                )
                
                # Створюємо кнопку "Читати далі"
                button = {"inline_keyboard": [[{"text": "📖 Читати далі", "url": f"https://lazysoft.dev{article.get_absolute_url('uk')}"}]]}
                
                self.stdout.write(f"\n📝 Повідомлення:")
                self.stdout.write("-" * 30)
                self.stdout.write(message)
                self.stdout.write("-" * 30)
                
                self.stdout.write(f"\n🖼️ Зображення: {article.ai_image_url}")
                self.stdout.write(f"🔗 URL: {article.get_absolute_url('uk')}")
                
                if not options['dry_run']:
                    # Публікуємо в Telegram
                    telegram_service = TelegramService()
                    external_id = telegram_service.post_to_telegram(
                        message, 
                        photo_url=article.ai_image_url,
                        language='uk',
                        reply_markup=button
                    )
                    
                    if external_id:
                        self.stdout.write(f"✅ Успішно опубліковано! ID: {external_id}")
                    else:
                        self.stdout.write("❌ Не вдалося опублікувати")
                else:
                    self.stdout.write("⚠️ DRY RUN - публікація пропущена")
                    
            except ProcessedArticle.DoesNotExist:
                self.stdout.write("❌ Статтю не знайдено")
        else:
            self.stdout.write("❌ Вкажіть --article-id")
