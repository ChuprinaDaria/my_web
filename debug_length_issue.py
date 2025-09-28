#!/usr/bin/env python
import os
import django

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import ProcessedArticle
from django.utils import timezone

def debug_length_issue():
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
    
    # Перевіряємо всі поля на довжину
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
    
    button_url = f"https://lazysoft.dev{article_to_post.get_absolute_url('uk')}"
    
    print(f"📏 title: {len(title)}")
    print(f"📏 summary: {len(summary)}")
    print(f"📏 message: {len(message)}")
    print(f"📏 button_url: {len(button_url)}")
    print(f"📏 ai_image_url: {len(article_to_post.ai_image_url or '')}")
    
    print(f"\n🔗 Button URL: {button_url}")
    
    if len(button_url) > 200:
        print(f"⚠️ Button URL перевищує 200 символів!")
    
    if len(message) > 4096:
        print(f"⚠️ Message перевищує ліміт Telegram (4096)!")

if __name__ == "__main__":
    debug_length_issue()
