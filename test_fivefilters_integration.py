#!/usr/bin/env python3
"""
Тестуємо FiveFilters інтеграцію з конкретною статтею
"""

import os
import sys
import django

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.services.fulltext_extractor import FullTextExtractor
from news.services.rss_parser import RSSParser
from news.models import RSSSource, RawArticle

def test_normal_news_site():
    """Тестуємо на звичайному новинному сайті"""
    print("🔍 Тест на звичайному новинному сайті")
    print("=" * 50)
    
    # Беремо TechCrunch - там точно є повні статті
    techcrunch = RSSSource.objects.filter(
        name__icontains='TechCrunch',
        is_active=True
    ).first()
    
    if not techcrunch:
        print("❌ TechCrunch не знайдено. Спробуємо будь-яке EN джерело...")
        techcrunch = RSSSource.objects.filter(
            language='en',
            is_active=True
        ).exclude(name__icontains='Weekly').first()
    
    if not techcrunch:
        print("❌ Немає підходящих джерел")
        return
    
    print(f"📰 Тестуємо: {techcrunch.name}")
    print(f"🔗 URL: {techcrunch.url}")
    
    # Парсимо RSS
    parser = RSSParser()
    try:
        result = parser.parse_single_source(techcrunch)
        print(f"📊 RSS результат: {result}")
        
        # Беремо першу статтю
        latest = RawArticle.objects.filter(
            source=techcrunch
        ).order_by('-fetched_at').first()
        
        if not latest:
            print("❌ Статті не знайдено")
            return
            
        print(f"\n📰 Тестова стаття: {latest.title[:70]}...")
        print(f"🔗 URL статті: {latest.url}")
        
        # RSS контент
        rss_content = latest.content or latest.summary or ""
        print(f"📏 RSS контент: {len(rss_content)} символів")
        
        if rss_content:
            print(f"\n📄 RSS початок:")
            print("-" * 30)
            print(rss_content[:200] + "..." if len(rss_content) > 200 else rss_content)
            print("-" * 30)
        
        return latest.url
        
    except Exception as e:
        print(f"❌ Помилка RSS: {e}")
        return None

def test_fivefilters_extraction(article_url):
    """Тестуємо FiveFilters витягування"""
    if not article_url:
        print("❌ Немає URL для тестування")
        return
        
    print(f"\n🔍 Тест FiveFilters")
    print("=" * 30)
    print(f"🔗 URL: {article_url}")
    
    # Ініціалізуємо extractor
    extractor = FullTextExtractor()
    
    try:
        # Витягуємо повний текст
        print("⏳ Витягування повного тексту...")
        full_content = extractor.extract_article(article_url)
        
        if full_content:
            print(f"✅ FiveFilters контент: {len(full_content)} символів")
            
            print(f"\n📄 FiveFilters початок:")
            print("-" * 30)
            print(full_content[:300] + "..." if len(full_content) > 300 else full_content)
            print("-" * 30)
            
            # Порівняння
            return full_content
        else:
            print("❌ FiveFilters не зміг витягти контент")
            return None
            
    except Exception as e:
        print(f"❌ Помилка FiveFilters: {e}")
        return None

def compare_content_quality(rss_content, full_content):
    """Порівнюємо якість контенту"""
    print(f"\n📊 ПОРІВНЯННЯ ЯКОСТІ")
    print("=" * 30)
    
    if not rss_content:
        rss_content = ""
    if not full_content:
        full_content = ""
    
    print(f"📏 RSS довжина: {len(rss_content)} символів")
    print(f"📏 FiveFilters довжина: {len(full_content)} символів")
    
    improvement = len(full_content) - len(rss_content)
    if improvement > 0:
        percentage = (improvement / len(rss_content)) * 100 if len(rss_content) > 0 else 999
        print(f"📈 Покращення: +{improvement} символів (+{percentage:.1f}%)")
        
        if improvement > 1000:
            print("🎉 ВІДМІННО! FiveFilters дає НАБАГАТО більше контенту")
        elif improvement > 500:
            print("✅ ДОБРЕ! FiveFilters покращує контент")
        else:
            print("⚠️ Невелике покращення")
    else:
        print("❌ FiveFilters не покращив контент")

def test_manual_url():
    """Тест з ручним URL"""
    print(f"\n🔍 Ручний тест FiveFilters")
    print("=" * 30)
    
    # Спочатку перевіримо доступність FiveFilters
    import requests
    try:
        response = requests.get("http://localhost:8082", timeout=5)
        print(f"✅ FiveFilters доступний: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ FiveFilters недоступний: {e}")
        return False
    
    # Простий URL для тестування
    test_urls = [
        "https://arstechnica.com/gadgets/2024/11/",
        "https://www.reuters.com/technology/",
        "https://www.bbc.com/news/technology"
    ]
    
    extractor = FullTextExtractor()
    
    for test_url in test_urls:
        print(f"\n🔗 Тест URL: {test_url}")
        
        try:
            # Прямий тест через requests
            response = requests.get(
                f"http://localhost:8082/extract.php",
                params={'url': test_url, 'format': 'json'},
                timeout=30
            )
            
            print(f"📊 HTTP статус: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    content = data.get('content', '')
                    if content:
                        print(f"✅ Успіх! {len(content)} символів")
                        print(f"📄 Початок: {content[:150]}...")
                        return True
                    else:
                        print("⚠️ Порожній контент")
                except Exception as e:
                    print(f"⚠️ JSON помилка: {e}")
                    print(f"📄 Response: {response.text[:200]}...")
            else:
                print(f"❌ HTTP помилка: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Помилка запиту: {e}")
    
    return False

def main():
    print("🧪 LAZYSOFT - Тест FiveFilters інтеграції")
    print("=" * 50)
    
    # 1. Тест звичайного RSS
    article_url = test_normal_news_site()
    
    # 2. Тест FiveFilters
    if article_url:
        full_content = test_fivefilters_extraction(article_url)
        
        # 3. Порівняння (потрібно взяти RSS контент з попереднього тесту)
        # Цей крок зробимо вручну через обмеження
        
    # 4. Ручний тест на відомому URL
    manual_success = test_manual_url()
    
    print(f"\n🎯 РЕЗУЛЬТАТ:")
    print("-" * 20)
    if manual_success:
        print("✅ FiveFilters працює! Готові до інтеграції!")
    else:
        print("❌ Проблеми з FiveFilters. Перевір налаштування.")

if __name__ == "__main__":
    main()