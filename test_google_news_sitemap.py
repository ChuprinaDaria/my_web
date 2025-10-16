#!/usr/bin/env python3
"""
Тест Google News Sitemap
"""
import os
import sys
import django

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_google_news_sitemap():
    """Тестує Google News sitemap"""
    print("🧪 Тестування Google News Sitemap...")
    
    client = Client()
    
    # Тестуємо основний sitemap
    print("\n1. Тестуємо основний sitemap...")
    response = client.get('/sitemap.xml')
    print(f"   Статус: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Основний sitemap працює")
    else:
        print("   ❌ Проблема з основним sitemap")
        print(f"   Відповідь: {response.content.decode()[:200]}...")
    
    # Тестуємо Google News sitemap
    print("\n2. Тестуємо Google News sitemap...")
    response = client.get('/news-sitemap.xml')
    print(f"   Статус: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Google News sitemap працює")
        content = response.content.decode()
        print(f"   Розмір відповіді: {len(content)} символів")
        
        # Перевіряємо наявність ключових тегів
        if 'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"' in content:
            print("   ✅ Google News namespace присутній")
        else:
            print("   ❌ Google News namespace відсутній")
            
        if '<news:news>' in content:
            print("   ✅ news:news теги присутні")
        else:
            print("   ❌ news:news теги відсутні")
            
        if '<news:publication>' in content:
            print("   ✅ news:publication теги присутні")
        else:
            print("   ❌ news:publication теги відсутні")
            
        print(f"\n   Прев'ю контенту:")
        print("   " + content[:500] + "...")
        
    else:
        print("   ❌ Проблема з Google News sitemap")
        print(f"   Відповідь: {response.content.decode()[:200]}...")
    
    # Тестуємо news sitemap
    print("\n3. Тестуємо news sitemap...")
    response = client.get('/sitemap-news.xml')
    print(f"   Статус: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ News sitemap працює")
    else:
        print("   ❌ Проблема з news sitemap")
        print(f"   Відповідь: {response.content.decode()[:200]}...")

if __name__ == "__main__":
    test_google_news_sitemap()
