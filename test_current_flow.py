#!/usr/bin/env python3
"""
Тестуємо поточний flow: RSS → AI без FiveFilters
"""

import os
import sys
import django

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.services.rss_parser import RSSParser
from news.models import RSSSource, RawArticle

def test_current_rss_content():
    """Перевіряємо що зараз парситься з RSS"""
    print("🔍 Тест поточного RSS контенту")
    print("=" * 50)
    
    # Беремо активне англійське джерело
    source = RSSSource.objects.filter(is_active=True, language='en').first()
    if not source:
        print("❌ Немає активних англійських джерел")
        return
    
    print(f"📰 Тестуємо: {source.name}")
    print(f"🔗 URL: {source.url}")
    
    # Парсимо RSS
    parser = RSSParser()
    try:
        result = parser.parse_single_source(source)
        print(f"📊 Результат парсингу: {result}")
        
        # Беремо останню статтю
        latest = RawArticle.objects.filter(source=source).order_by('-fetched_at').first()
        
        if not latest:
            print("❌ Статті не знайдено")
            return
            
        print(f"\n📰 Остання стаття: {latest.title[:50]}...")
        print(f"📏 Довжина content: {len(latest.content or '')} символів")
        print(f"📏 Довжина summary: {len(latest.summary or '')} символів")
        
        # Показуємо початок контенту
        content = latest.content or latest.summary or ""
        if content:
            print(f"\n📄 Початок контенту:")
            print("-" * 30)
            print(content[:300] + "..." if len(content) > 300 else content)
            print("-" * 30)
            
            # Аналізуємо якість контенту
            if len(content) < 200:
                print("⚠️ ПРОБЛЕМА: Контент дуже короткий - лише заголовок/уривок!")
                print("💡 Тут саме допоможе FiveFilters для повного тексту")
            elif len(content) < 500:
                print("⚠️ Контент короткий - можливо неповний")
            else:
                print("✅ Контент нормальної довжини")
                
        else:
            print("❌ Контент порожній!")
            
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")

def check_ai_processing_ready():
    """Перевіряємо готовність до AI обробки"""
    print("\n🤖 Перевірка готовності AI")
    print("=" * 30)
    
    # Перевіряємо необроблені статті
    unprocessed = RawArticle.objects.filter(is_processed=False).count()
    print(f"📊 Необроблених статей: {unprocessed}")
    
    if unprocessed > 0:
        # Беремо першу для аналізу
        first = RawArticle.objects.filter(is_processed=False).first()
        print(f"📰 Перша необроблена: {first.title[:50]}...")
        
        # Оцінюємо якість контенту для AI
        content_length = len(first.content or first.summary or "")
        print(f"📏 Довжина контенту: {content_length} символів")
        
        if content_length < 300:
            print("⚠️ AI працюватиме з мінімальним контентом")
            print("💡 FiveFilters збільшить якість AI обробки!")
        else:
            print("✅ Достатньо контенту для AI")
    else:
        print("ℹ️ Немає статей для обробки")

def main():
    print("🧪 LAZYSOFT - Тест поточного flow")
    print("=" * 50)
    
    # Тестуємо RSS контент
    test_current_rss_content()
    
    # Перевіряємо готовність AI
    check_ai_processing_ready()
    
    print("\n🎯 ВИСНОВКИ:")
    print("-" * 20)
    print("1. Спочатку перевіримо якість RSS контенту")
    print("2. Потім інтегруємо FiveFilters для повного тексту")
    print("3. Нарешті протестуємо AI з покращеним контентом")

if __name__ == "__main__":
    main()