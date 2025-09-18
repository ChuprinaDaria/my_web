# 🔒 Налаштування безпеки для Lazysoft

## Виконані кроки

### 1. Content Security Policy (CSP)
✅ Створено `SecurityHeadersMiddleware` в `core/middleware/security_headers.py`
✅ Додано CSP з Trusted Types для захисту від DOM-based XSS
✅ Налаштовано дозволи для Google Analytics, Google Fonts, та зовнішніх зображень

### 2. HTTP Strict Transport Security (HSTS)
✅ Додано HSTS заголовок з `max-age=31536000`, `includeSubDomains` та `preload`
✅ Активується тільки в production режимі (коли `DEBUG=False`)

### 3. Додаткові заголовки безпеки
✅ `X-Content-Type-Options: nosniff`
✅ `X-Frame-Options: DENY`
✅ `X-XSS-Protection: 1; mode=block`
✅ `Referrer-Policy: strict-origin-when-cross-origin`
✅ `Permissions-Policy` для обмеження доступу до API
✅ `Cross-Origin-Embedder-Policy: require-corp`
✅ `Cross-Origin-Opener-Policy: same-origin`
✅ `Cross-Origin-Resource-Policy: same-origin`

## Команди для тестування

### 1. Запустіть сервер розробки:
```bash
python manage.py runserver
```

### 2. Тестуйте безпекові заголовки:
```bash
python manage.py test_security_headers
```

### 3. Тестуйте з власним URL:
```bash
python manage.py test_security_headers --url https://yourdomain.com
```

## Перевірка в браузері

1. Відкрийте Developer Tools (F12)
2. Перейдіть на вкладку Network
3. Перезавантажте сторінку
4. Клікніть на перший запит (зазвичай HTML документ)
5. Перевірте вкладку Headers на наявність безпекових заголовків

## Налаштування для production

### 1. Оновіть налаштування в `.env`:
```env
DEBUG=False
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### 2. Налаштуйте HTTPS на сервері
- Отримайте SSL сертифікат (Let's Encrypt, Cloudflare, тощо)
- Налаштуйте редирект з HTTP на HTTPS
- Перевірте, що всі ресурси завантажуються через HTTPS

### 3. Додаткові рекомендації
- Регулярно оновлюйте залежності
- Використовуйте сильні паролі
- Налаштуйте моніторинг безпеки
- Регулярно перевіряйте логи на підозрілу активність

## Структура файлів

```
core/
├── middleware/
│   ├── __init__.py
│   ├── security.py (існуючий)
│   └── security_headers.py (новий)
└── management/
    └── commands/
        └── test_security_headers.py (новий)
```

## Примітки

- CSP може потребувати налаштування після додавання нових зовнішніх скриптів
- Trusted Types вимагає додаткового налаштування для складних JavaScript додатків
- HSTS працює тільки через HTTPS
- Деякі заголовки можуть конфліктувати з CDN (Cloudflare, тощо)
