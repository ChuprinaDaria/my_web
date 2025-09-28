#!/usr/bin/env python
import os
import django

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle, SocialMediaPost
from django.utils import timezone

def test_exact_error():
    today = timezone.now().date()
    
    # Знаходимо наступну статтю для публікації
    article_to_post = (ProcessedArticle.objects
        .filter(status='published', is_top_article=True, top_selection_date=today)
        .exclude(social_posts__platform='telegram_uk', social_posts__status='published')
        .order_by('article_rank')
        .first())
    
    if not article_to_post:
        print("❌ Немає статей для публікації")
        return
    
    print(f"📰 Стаття: {article_to_post.title_uk[:50]}...")
    
    # Готуємо дані точно як в завданні
    title = article_to_post.title_uk[:200] if article_to_post.title_uk else article_to_post.title_en[:200]
    
    if article_to_post.summary_uk and article_to_post.summary_uk != article_to_post.summary_en:
        summary = article_to_post.summary_uk[:1000]
    elif article_to_post.business_insight_uk:
        summary = article_to_post.business_insight_uk[:1000] + "..."
    else:
        summary = article_to_post.summary_en[:1000]
    
    message = (
        f"🔥 <strong>{title}</strong>\n\n"
        f"{summary}\n\n"
        f"— <em>Lazysoft AI News</em>"
    )
    
    image_url = (article_to_post.ai_image_url[:200] if article_to_post.ai_image_url else '')
    
    print(f"📏 Перевірка довжин:")
    print(f"  - message: {len(message)}")
    print(f"  - image_url: {len(image_url)}")
    print(f"  - platform: {len('telegram_uk')}")
    print(f"  - status: {len('draft')}")
    
    # Тестуємо створення SocialMediaPost
    try:
        print("\n🧪 Тестуємо створення SocialMediaPost...")
        
        smp = SocialMediaPost(
            article=article_to_post,
            platform='telegram_uk',
            content=message,
            image_url=image_url,
            status='draft'
        )
        
        # Не зберігаємо, просто перевіряємо валідацію
        smp.full_clean()
        print("✅ Валідація пройшла успішно")
        
        # Тепер спробуємо зберегти
        smp.save()
        print(f"✅ SocialMediaPost створено: {smp.id}")
        
        # Видаляємо тестовий запис
        smp.delete()
        print("🗑️ Тестовий запис видалено")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exact_error()
