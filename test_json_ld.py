#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки JSON-LD templatetag
"""

import os
import sys
import django

# Додаємо шлях до проєкту
sys.path.append('/home/dchuprina/Desktop/Lazysoft')

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from news.templatetags.seo_tags import news_json_ld
from news.models import ProcessedArticle
from django.template import Context, Template

def test_json_ld():
    """Тестуємо JSON-LD templatetag"""
    print("🧪 Тестуємо JSON-LD templatetag...")
    
    try:
        # Отримуємо першу статтю
        article = ProcessedArticle.objects.first()
        
        if not article:
            print("❌ Немає статей в базі даних")
            return
        
        print(f"✅ Знайдено статтю: {article.get_title('uk')}")
        
        # Створюємо контекст
        context = Context({
            'request': None,
            'article': article
        })
        
        # Тестуємо templatetag
        result = news_json_ld(context, article)
        
        print("✅ JSON-LD згенеровано успішно!")
        print(f"📄 Розмір JSON: {len(result['schema_json'])} символів")
        
        # Показуємо прев'ю JSON
        json_preview = result['schema_json'][:500] + "..." if len(result['schema_json']) > 500 else result['schema_json']
        print(f"\n📋 Прев'ю JSON-LD:")
        print(json_preview)
        
        # Перевіряємо наявність ключових полів
        json_str = result['schema_json']
        required_fields = [
            '@context',
            '@type',
            'headline',
            'datePublished',
            'author',
            'publisher'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in json_str:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Відсутні поля: {', '.join(missing_fields)}")
        else:
            print("✅ Всі обов'язкові поля присутні")
            
        # Перевіряємо логотип
        if 'logo.svg' in json_str:
            print("✅ Логотип правильно налаштований")
        else:
            print("❌ Логотип не знайдено в JSON")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_ld()
