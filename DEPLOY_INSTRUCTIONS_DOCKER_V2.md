# 🚀 Інструкції для деплою (Docker Compose V2)

## ⚡ Швидкий деплой (одна команда)

```bash
cd /opt/lazysoft && \
git fetch origin && \
git checkout claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt && \
git pull origin claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt && \
docker compose down && \
docker compose build --no-cache web celery && \
docker compose up -d && \
sleep 15 && \
docker compose exec web python manage.py migrate && \
docker compose logs --tail=100 web celery
```

---

## 📋 Покрокові команди

### 1. Перейти в директорію проекту
```bash
cd /opt/lazysoft
```

### 2. Отримати останні зміни з Git
```bash
git fetch origin
git checkout claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt
git pull origin claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt
```

### 3. Зупинити контейнери
```bash
docker compose down
```

### 4. Перебудувати контейнери (ВАЖЛИВО!)
```bash
docker compose build --no-cache web celery
```

### 5. Запустити контейнери
```bash
docker compose up -d
```

### 6. Почекати 10-15 секунд
```bash
sleep 15
```

### 7. Застосувати міграції
```bash
# Всі міграції разом
docker compose exec web python manage.py migrate

# Або окремо по app:
docker compose exec web python manage.py migrate hr
docker compose exec web python manage.py migrate rag
docker compose exec web python manage.py migrate news
```

### 8. Перевірити статус
```bash
# Статус контейнерів
docker compose ps

# Логи web
docker compose logs -f --tail=100 web

# Логи celery
docker compose logs -f --tail=100 celery
```

---

## 🔍 Перевірка після деплою

### 1. Перевірити міграції
```bash
docker compose exec web python manage.py showmigrations | grep "\[ \]"
```
**Очікується**: порожній вивід (всі міграції застосовані)

### 2. Перевірити NewsCategory помилки
```bash
docker compose logs celery | grep -i "newscategory\|fielderror" | tail -20
```
**Очікується**: немає помилок про title_en, title_pl, title_uk

### 3. Перевірити Google Bot (через 15-20 хвилин)
```bash
tail -f /opt/lazysoft/logs/security.log
```
**Очікується**: немає "fake_bot" для IP 192.178.* або 2001:4860:*

```bash
# Перевірка за останні записи
grep "fake_bot" /opt/lazysoft/logs/security.log | grep -E "(192.178|2001:4860)" | tail -20
```
**Очікується**: порожній вивід або старі записи

### 4. Перевірити сайт
```bash
curl -I https://lazysoft.pl
```
**Очікується**: HTTP 200 OK

```bash
curl https://lazysoft.pl/sitemap.xml | head -20
```
**Очікується**: XML sitemap

---

## 🛠️ Корисні команди для діагностики

### Перегляд логів в реальному часі
```bash
# Web логи
docker compose logs -f web

# Celery логи
docker compose logs -f celery

# Обидва разом
docker compose logs -f web celery
```

### Перевірка міграцій
```bash
# Всі міграції
docker compose exec web python manage.py showmigrations

# Тільки news app
docker compose exec web python manage.py showmigrations news

# Тільки незастосовані
docker compose exec web python manage.py showmigrations | grep "\[ \]"
```

### Перезапуск конкретного сервісу
```bash
# Перезапустити тільки web
docker compose restart web

# Перезапустити тільки celery
docker compose restart celery

# Перезапустити все
docker compose restart
```

### Django shell для тестування
```bash
docker compose exec web python manage.py shell
```

```python
# В shell перевірте NewsCategory
from news.models import NewsCategory
cats = NewsCategory.objects.all()
print(cats.count())
print(cats.first().__dict__)
```

---

## ⚠️ Можливі проблеми

### Проблема 1: "Error response from daemon: No such container"
```bash
docker compose ps
docker compose up -d
```

### Проблема 2: Міграції не застосовуються
```bash
# Перевірте чи контейнер запущений
docker compose ps | grep web

# Перезапустіть контейнер
docker compose restart web
sleep 10
docker compose exec web python manage.py migrate
```

### Проблема 3: Port already in use
```bash
# Знайдіть процес
sudo lsof -i :8000

# Або зупиніть все
docker compose down
docker stop $(docker ps -aq)
docker compose up -d
```

### Проблема 4: Build fails
```bash
# Очистіть кеш Docker
docker system prune -a
docker compose build --no-cache web celery
```

---

## 📊 Що виправлено в цьому релізі

### 1. NewsCategory Migrations ✅
- Видалено застарілий `cta_link` field
- Додано empty migrations для hr та rag
- Виправлено setup_rss_sources.py

### 2. Google Bot Blocking ✅
- Реалізовано reverse DNS verification
- Видалено 200+ рядків застарілих IP ranges
- Автоматична підтримка нових Google IP
- Захист від спуфінгу

### 3. SEO ✅
- robots.txt налаштовано правильно
- Sitemaps доступні
- Індексація працює повністю

---

## 🎯 Очікувані результати

✅ Міграції застосовані без помилок
✅ AI процесор працює без NewsCategory errors
✅ Google боти не блокуються (немає fake_bot в логах)
✅ Сайт доступний та працює
✅ Celery обробляє новини без помилок

---

**Створено**: 2025-10-30
**Версія Docker**: Docker Compose V2
**Branch**: `claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt`
