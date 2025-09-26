# Schema.org Documentation для Lazysoft

## 📋 Огляд

Цей документ описує структуровану розмітку Schema.org, яка використовується на сайті Lazysoft для покращення SEO та відображення в пошукових системах.

## 🏗️ Структура

### Централізований файл
- **Файл**: `core/templates/core/includes/schema_org.html`
- **Підключення**: В `core/templates/core/base.html`
- **Контекст**: Доступний у всіх шаблонах через `seo_settings` context processor

### Основні типи Schema.org

#### 1. Organization Schema
```json
{
  "@type": "Organization",
  "@id": "{{ SITE_URL }}#organization",
  "name": "{{ SITE_NAME }}",
  "url": "{{ SITE_URL }}",
  "logo": {...},
  "description": "...",
  "foundingDate": "2023",
  "numberOfEmployees": "1-10",
  "areaServed": [...],
  "serviceType": [...],
  "address": {...},
  "contactPoint": [...],
  "sameAs": [...]
}
```

#### 2. WebSite Schema
```json
{
  "@type": "WebSite",
  "@id": "{{ SITE_URL }}#website",
  "name": "{{ SITE_NAME }}",
  "url": "{{ SITE_URL }}",
  "publisher": {...},
  "potentialAction": {...},
  "inLanguage": ["uk", "pl", "en"]
}
```

#### 3. BreadcrumbList Schema
```json
{
  "@type": "BreadcrumbList",
  "itemListElement": [...]
}
```

## 🎯 Умовна розмітка

### Для статей новин
- **Умова**: `{% if article %}`
- **Тип**: `Article`
- **Поля**: headline, description, image, datePublished, author, publisher, etc.

### Для проектів
- **Умова**: `{% if project %}`
- **Тип**: `Service`
- **Поля**: name, description, provider, offers, serviceType, etc.

### Для категорій послуг
- **Умова**: `{% if service_category %}`
- **Тип**: `Service`
- **Поля**: name, description, provider, serviceType, areaServed, etc.

### Для головної сторінки
- **Умова**: `{% if page_type == 'home' %}`
- **Тип**: `Service`
- **Поля**: name, description, provider, areaServed, hasOfferCatalog, etc.

### Для сторінки контактів
- **Умова**: `{% if page_type == 'contact' %}`
- **Тип**: `LocalBusiness`
- **Поля**: name, description, url, telephone, email, address, geo, etc.

### Для FAQ сторінок
- **Умова**: `{% if faqs %}`
- **Тип**: `FAQPage`
- **Поля**: mainEntity (масив Question/Answer)

## 🌐 Багатомовність

### Підтримувані мови
- **Українська** (`uk`)
- **Польська** (`pl`) 
- **Англійська** (`en`)

### Динамічний контент
```django
{% if LANGUAGE_CODE == 'uk' %}Український текст
{% elif LANGUAGE_CODE == 'pl' %}Polski tekst
{% else %}English text{% endif %}
```

## 🔧 Контекст процесор

### `seo_settings` context processor
Додає до контексту:
- `SITE_URL` - URL сайту
- `SITE_NAME` - Назва сайту
- `page_type` - Тип сторінки (home, news, projects, services, contact, about)
- `breadcrumbs` - Масив breadcrumbs для навігації

### Автоматичне визначення типу сторінки
```python
if '/news/' in path:
    page_type = 'news'
elif '/projects/' in path:
    page_type = 'projects'
elif '/services/' in path:
    page_type = 'services'
elif '/contact' in path:
    page_type = 'contact'
elif '/about' in path:
    page_type = 'about'
```

## 📊 Переваги

### SEO покращення
- ✅ Покращене відображення в пошукових результатах
- ✅ Rich snippets в Google
- ✅ Структуровані дані для пошукових систем
- ✅ Підтримка Knowledge Graph

### Локальний пошук
- ✅ LocalBusiness schema для контактної сторінки
- ✅ Геолокація та адреса
- ✅ Контактна інформація
- ✅ Години роботи

### E-commerce готовність
- ✅ Service schema з offers
- ✅ PriceRange підтримка
- ✅ Availability статуси
- ✅ Currency підтримка

## 🧪 Тестування

### Валідація
1. Відкрийте сайт у браузері
2. Перейдіть на [validator.schema.org](https://validator.schema.org/)
3. Вставте URL сторінки або HTML код
4. Перевірте наявність помилок

### Тестовий файл
- **Файл**: `test_schema.html`
- **Призначення**: Тестування schema.org розмітки
- **Використання**: Відкрийте у браузері та перевірте валідатором

## 🔄 Оновлення

### Додавання нових типів сторінок
1. Додайте умову в `schema_org.html`
2. Оновіть `seo_settings` context processor
3. Додайте відповідний schema тип

### Додавання нових полів
1. Оновіть відповідний JSON-LD блок
2. Перевірте валідність на validator.schema.org
3. Протестуйте на різних сторінках

## 📝 Примітки

- Всі JSON-LD блоки мають правильний синтаксис
- Використовуються escapejs фільтри для безпеки
- Підтримується багатомовність
- Автоматичне визначення типу сторінки
- Централізоване управління через один файл
