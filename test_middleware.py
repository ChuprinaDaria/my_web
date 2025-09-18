#!/usr/bin/env python
"""
Простий тест для перевірки SecurityHeadersMiddleware
"""
import os
import sys
import django
from django.test import RequestFactory
from django.http import HttpResponse

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazysoft.settings')
django.setup()

from core.middleware.security_headers import SecurityHeadersMiddleware

def test_security_headers():
    print("🔒 Тестуємо SecurityHeadersMiddleware...")
    
    # Створюємо тестові об'єкти
    factory = RequestFactory()
    request = factory.get('/')
    response = HttpResponse("Test response")
    
    # Створюємо middleware
    middleware = SecurityHeadersMiddleware(lambda req: response)
    
    # Обробляємо відповідь
    processed_response = middleware.process_response(request, response)
    
    # Перевіряємо заголовки
    headers_to_check = [
        'Content-Security-Policy',
        'Strict-Transport-Security',
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Referrer-Policy',
        'Permissions-Policy'
    ]
    
    print("\n📋 Результати тестування:")
    print("=" * 50)
    
    for header in headers_to_check:
        if header in processed_response:
            value = processed_response[header]
            print(f"✅ {header}: {value[:80]}{'...' if len(value) > 80 else ''}")
        else:
            print(f"❌ {header}: ВІДСУТНІЙ")
    
    print(f"\n🎯 Всього заголовків: {len(processed_response._headers)}")
    print(f"🔍 DEBUG режим: {os.environ.get('DJANGO_DEBUG', 'True')}")

if __name__ == '__main__':
    test_security_headers()
