#!/usr/bin/env python3
"""
Тестуємо повну інтеграцію: FiveFilters + AI обробка
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import RawArticle, ProcessedArticle
from news.services.ai_processor import AINewsProcessor

def test_full_pipeline():
    """Тестуємо повний pipeline з FiveFilters"""
    print("🔄 ТЕСТ ПОВНОЇ ІНТЕГРАЦІЇ")
    print("=" * 40)
    
    # Беремо необроблену статтю
    article = RawArticle.objects.filter(
        is_processed=False,
        is_duplicate=False
    ).first()
    
    if not article:
        print("❌ Немає необроблених статей")
        return
    
    print(f"📰 Тестова стаття: {article.title[:50]}...")
    print(f"🔗 URL: {article.original_url}")
    
    # Показуємо оригінальний контент
    original_length = len(article.content or "")
    print(f"📏 Оригінальний контент: {original_length} символів")
    
    # Запускаємо AI процесор (тепер з FiveFilters)
    processor = AINewsProcessor()
    
    print(f"\n🤖 Запуск AI обробки з FiveFilters...")
    result = processor.process_article(article)
    
    if result:
        print("✅ AI обробка успішна!")
        
        # Перевіряємо чи збільшився контент
        enhanced_length = len(article.content or "")
        improvement = enhanced_length - original_length
        
        print(f"📈 FiveFilters покращення: +{improvement} символів")
        print(f"📏 Фінальний контент: {enhanced_length} символів")
        
        # Аналізуємо AI результат
        print(f"\n📊 AI результат:")
        print(f"🇺🇦 Заголовок: {result.title_uk}")
        print(f"📏 Summary довжина: {len(result.summary_uk)} символів")
        print(f"💡 Insight: {result.business_insight_uk[:100]}...")
        
        if improvement > 1000:
            print("🎉 ВІДМІННО! FiveFilters + AI працюють разом!")
        else:
            print("⚠️ FiveFilters не збагатив або стаття вже була збагачена")
    else:
        print("❌ AI обробка невдала")

if __name__ == "__main__":
    test_full_pipeline()

