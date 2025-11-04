# Виправлення Sitemap

## Проблеми, які були виявлені

1. **example.com замість lazysoft.pl** - в базі даних Django Sites framework був налаштований домен example.com
2. **Script теги в sitemap** - браузерні розширення додавали script теги до XML sitemap

## Виправлення

### 1. Виправлення домену (автоматично)

Створено міграцію, яка автоматично виправить домен при запуску:

```bash
python manage.py migrate
```

Міграція: `core/migrations/0005_fix_site_domain.py`

### 2. Ручне виправлення домену (опціонально)

Якщо потрібно виправити домен вручну:

```bash
python manage.py fix_site_domain
```

Команда: `core/management/commands/fix_site_domain.py`

### 3. Очищення script тегів

Middleware автоматично видаляє всі script теги з sitemap відповідей.

Файл: `core/middleware/sitemap_robots.py`

## Перевірка

Після виправлення перевірте sitemap:

- https://lazysoft.pl/sitemap.xml
- https://lazysoft.pl/sitemap-static.xml
- https://lazysoft.pl/sitemap-news.xml
- https://lazysoft.pl/sitemap-projects.xml
- https://lazysoft.pl/sitemap-articles.xml
- https://lazysoft.pl/news-sitemap-uk.xml
- https://lazysoft.pl/news-sitemap-pl.xml
- https://lazysoft.pl/news-sitemap-en.xml

## Що було змінено

1. **Міграція**: `core/migrations/0005_fix_site_domain.py` - автоматично оновлює домен в базі даних
2. **Команда**: `core/management/commands/fix_site_domain.py` - для ручного виправлення
3. **Middleware**: `core/middleware/sitemap_robots.py` - видаляє script теги з sitemap

## Налаштування в .env

Переконайтеся, що у вашому `.env` файлі правильно налаштовано:

```env
SITE_URL=https://lazysoft.pl
SITE_NAME=LAZYSOFT
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,lazysoft.pl,www.lazysoft.pl
```

## Google Search Console

Після виправлення:

1. Зайдіть в Google Search Console
2. Перейдіть в розділ Sitemaps
3. Перевідправте всі sitemap файли
4. Зачекайте, поки Google переіндексує сайт

Помилки "example.com" повинні зникнути протягом кількох днів.
