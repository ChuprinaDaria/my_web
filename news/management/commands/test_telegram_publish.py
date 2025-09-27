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
                # Заголовок завжди беремо з title_uk або title_en
                title = article.title_uk[:250] if article.title_uk else article.title_en[:250]
                
                # Summary - якщо український summary порожній або такий же як англійський, використовуємо business_insight_uk
                if article.summary_uk and article.summary_uk != article.summary_en:
                    summary = article.summary_uk[:1024]
                elif article.business_insight_uk:
                    summary = article.business_insight_uk[:1024] + "..."
                else:
                    summary = article.summary_en[:1024]
                
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
                        # Створюємо запис про публікацію
                        from news.models import SocialMediaPost
                        smp, created = SocialMediaPost.objects.get_or_create(
                            article=article,
                            platform='telegram_uk',
                            defaults={
                                'content': message,
                                'image_url': article.ai_image_url[:200] if article.ai_image_url else '',
                                'status': 'draft'
                            }
                        )
                        smp.mark_as_published(external_id)
                        self.stdout.write(f"✅ Успішно опубліковано! ID: {external_id}")
                        self.stdout.write(f"✅ SocialMediaPost створено: ID={smp.id}, Status={smp.status}")
                    else:
                        self.stdout.write("❌ Не вдалося опублікувати")
                else:
                    self.stdout.write("⚠️ DRY RUN - публікація пропущена")
                    
            except ProcessedArticle.DoesNotExist:
                self.stdout.write("❌ Статтю не знайдено")
        else:
            self.stdout.write("❌ Вкажіть --article-id")
