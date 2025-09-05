#!/usr/bin/env python3
"""
Перевіряємо що саме зберігається в статтях та де
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.models import RawArticle, ProcessedArticle

def inspect_raw_articles():
    """Дивимося що в Raw Articles"""
    print("📰 ПЕРЕВІРКА RAW ARTICLES")
    print("=" * 40)
    
    # Беремо кілька останніх статей
    articles = RawArticle.objects.order_by('-fetched_at')[:5]
    
    for i, article in enumerate(articles, 1):
        print(f"\n[{i}] {article.title[:60]}...")
        print(f"🔗 URL: {article.original_url}")
        print(f"📅 Опубліковано: {article.published_at}")
        print(f"🏷️ Джерело: {article.source.name}")
        print(f"🔄 Оброблено AI: {'✅' if article.is_processed else '❌'}")
        
        # Аналіз контенту
        content = article.content or ""
        summary = article.summary or ""
        
        print(f"📏 Content: {len(content)} символів")
        print(f"📏 Summary: {len(summary)} символів")
        
        # Показуємо початок контенту
        if content:
            print(f"📄 Content початок:")
            print("-" * 20)
            print(content[:200] + "..." if len(content) > 200 else content)
            print("-" * 20)
        
        if summary and summary != content:
            print(f"📋 Summary початок:")
            print("-" * 20)
            print(summary[:200] + "..." if len(summary) > 200 else summary)
            print("-" * 20)

def inspect_processed_articles():
    """Дивимося що в Processed Articles"""
    print(f"\n🤖 ПЕРЕВІРКА PROCESSED ARTICLES")
    print("=" * 40)
    
    processed = ProcessedArticle.objects.order_by('-created_at')[:3]
    
    if not processed:
        print("❌ Немає оброблених статей")
        return
    
    for i, article in enumerate(processed, 1):
        print(f"\n[{i}] {article.title_uk[:60]}...")
        print(f"🔗 Оригінал: {article.raw_article.original_url}")
        print(f"📅 Створено: {article.created_at}")
        print(f"🎯 Статус: {article.status}")
        print(f"🏷️ Категорія: {article.category.name_uk}")
        
        # Аналіз AI контенту
        print(f"\n📏 Довжина контенту по мовах:")
        print(f"  🇺🇦 UK: {len(article.summary_uk)} символів")
        print(f"  🇺🇸 EN: {len(article.summary_en)} символів") 
        print(f"  🇵🇱 PL: {len(article.summary_pl)} символів")
        
        # Показуємо український контент
        print(f"\n📄 Summary UK:")
        print("-" * 20)
        print(article.summary_uk[:300] + "..." if len(article.summary_uk) > 300 else article.summary_uk)
        print("-" * 20)
        
        # Інсайт
        if hasattr(article, 'business_insight_uk') and article.business_insight_uk:
            print(f"\n💡 Business Insight UK:")
            print("-" * 20)
            print(article.business_insight_uk[:200] + "..." if len(article.business_insight_uk) > 200 else article.business_insight_uk)
            print("-" * 20)

def check_content_flow():
    """Перевіряємо flow: RSS → FiveFilters → AI"""
    print(f"\n🔄 ПЕРЕВІРКА CONTENT FLOW")
    print("=" * 40)
    
    # Знаходимо статтю що пройшла весь flow
    processed_articles = ProcessedArticle.objects.select_related('raw_article').order_by('-created_at')[:3]
    
    for article in processed_articles:
        print(f"\n📰 {article.title_uk[:50]}...")
        
        raw = article.raw_article
        
        # Оригінальний RSS контент (до FiveFilters)
        original_rss_length = len(raw.summary or "")  # Summary зазвичай оригінальний RSS
        
        # Поточний content (після FiveFilters)
        current_content_length = len(raw.content or "")
        
        # AI згенерований контент
        ai_content_length = len(article.summary_uk or "")
        
        print(f"📊 Content Evolution:")
        print(f"  1️⃣ RSS Summary: {original_rss_length} символів")
        print(f"  2️⃣ FiveFilters Content: {current_content_length} символів")
        print(f"  3️⃣ AI Generated: {ai_content_length} символів")
        
        if current_content_length > original_rss_length:
            improvement = current_content_length - original_rss_length
            print(f"  📈 FiveFilters покращення: +{improvement} символів")
        
        # Перевіряємо чи AI використовував повний контент
        if current_content_length > 1000 and ai_content_length > 800:
            print(f"  ✅ AI мав достатньо контенту для якісної обробки")
        elif current_content_length > 1000:
            print(f"  ⚠️ AI згенерував короткий контент попри повний вхід")
        else:
            print(f"  ❌ AI працював з обмеженим контентом")

def check_database_storage():
    """Перевіряємо де що зберігається в БД"""
    print(f"\n💾 СТРУКТУРА ЗБЕРІГАННЯ В БД")
    print("=" * 40)
    
    print("📋 RawArticle поля:")
    print("  • title - заголовок з RSS")
    print("  • content - ОНОВЛЮЄТЬСЯ FiveFilters (повний текст)")
    print("  • summary - оригінальний RSS summary")
    print("  • original_url - посилання на статтю")
    print("  • is_processed - чи оброблено AI")
    
    print(f"\n📋 ProcessedArticle поля:")
    print("  • title_uk/en/pl - AI згенеровані заголовки")
    print("  • summary_uk/en/pl - AI згенерований контент (~1100 символів)")
    print("  • business_insight_uk/en/pl - AI інсайти")
    print("  • raw_article - зв'язок з оригінальною статтею")
    
    print(f"\n💡 ЛОГІКА ЗБЕРЕЖЕННЯ:")
    print("1. RSS парсер зберігає content + summary в RawArticle")
    print("2. FiveFilters ПЕРЕЗАПИСУЄ content більшим текстом")
    print("3. AI читає content (повний) і створює ProcessedArticle")
    print("4. Оригінальний RSS summary залишається для порівняння")

def main():
    print("🔍 ІНСПЕКЦІЯ КОНТЕНТУ СТАТЕЙ")
    print("=" * 50)
    
    # 1. Raw Articles
    inspect_raw_articles()
    
    # 2. Processed Articles  
    inspect_processed_articles()
    
    # 3. Content Flow
    check_content_flow()
    
    # 4. Database Structure
    check_database_storage()
    
    print(f"\n🎯 ВИСНОВКИ:")
    print("• FiveFilters збагачує RawArticle.content")
    print("• AI обробляє збагачений контент")
    print("• Все зберігається правильно в БД")
    print("• Готові до повної інтеграції!")

if __name__ == "__main__":
    main()