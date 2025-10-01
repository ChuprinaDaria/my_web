#!/usr/bin/env python
import os
import sys
import django

# Додаємо поточну директорію до Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings_local')
django.setup()

from core.sitemaps import StaticViewSitemap

def test_sitemap():
    print("🧪 Тестуємо StaticViewSitemap...")
    
    sitemap = StaticViewSitemap()
    
    print(f"📋 Items: {sitemap.items()}")
    print(f"🌐 i18n enabled: {sitemap.i18n}")
    print(f"⭐ Priority: {sitemap.priority}")
    print(f"🔄 Change freq: {sitemap.changefreq}")
    
    # Тестуємо location для першого item
    if sitemap.items():
        first_item = sitemap.items()[0]
        try:
            location = sitemap.location(first_item)
            print(f"📍 First location: {location}")
        except Exception as e:
            print(f"❌ Error getting location: {e}")
    
    print("✅ Тест завершено!")

if __name__ == "__main__":
    test_sitemap()
