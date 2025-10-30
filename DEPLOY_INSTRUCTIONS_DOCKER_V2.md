# 🚀 Інструкції для деплою (Docker Compose V2)

## ⚡ Швидкий деплой (одна команда)

```bash
cd /opt/lazysoft && \
git fetch origin && \
git checkout claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt && \
git pull origin claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt && \
docker compose -f docker-compose.prod.yml down && \
docker compose -f docker-compose.prod.yml build --no-cache web celery && \
docker compose -f docker-compose.prod.yml up -d && \
sleep 15 && \
docker compose -f docker-compose.prod.yml exec web pip install --no-cache-dir "pydyf==0.10.0" && \
docker compose -f docker-compose.prod.yml restart web && \
sleep 10 && \
docker compose -f docker-compose.prod.yml exec web python manage.py migrate hr 0005_contract_contract_number_employee_id_number_and_more --fake && \
docker compose -f docker-compose.prod.yml exec web python manage.py migrate && \
docker compose -f docker-compose.prod.yml logs --tail=100 web celery
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
docker compose -f docker-compose.prod.yml up -d
```

### 6. Почекати 10-15 секунд і встановити pydyf
```bash
sleep 15

# ВАЖЛИВО: Встановити pydyf для PDF генерації
docker compose -f docker-compose.prod.yml exec web pip install --no-cache-dir "pydyf==0.10.0"

# Перезапустити web після встановлення
docker compose -f docker-compose.prod.yml restart web

# Почекати після рестарту
sleep 10
```

### 7. Виправити конфлікт hr міграцій (fake-apply)
```bash
# Колонка contract_number вже є в БД, тому fake-apply
docker compose -f docker-compose.prod.yml exec web python manage.py migrate hr 0005_contract_contract_number_employee_id_number_and_more --fake
```

### 8. Застосувати міграції
```bash
# Всі міграції разом
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Або окремо по app:
docker compose -f docker-compose.prod.yml exec web python manage.py migrate hr
docker compose -f docker-compose.prod.yml exec web python manage.py migrate rag
docker compose -f docker-compose.prod.yml exec web python manage.py migrate news
```

### 9. Перевірити статус
```bash
# Статус контейнерів
docker compose -f docker-compose.prod.yml ps

# Логи web
docker compose -f docker-compose.prod.yml logs -f --tail=100 web

# Логи celery
docker compose -f docker-compose.prod.yml logs -f --tail=100 celery
```

---

## 🔍 Перевірка після деплою

### 1. Перевірити міграції
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations | grep "\[ \]"
```
**Очікується**: порожній вивід (всі міграції застосовані)

### 2. Перевірити NewsCategory помилки
```bash
docker compose -f docker-compose.prod.yml logs celery | grep -i "newscategory\|fielderror" | tail -20
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
docker compose -f docker-compose.prod.yml logs -f web

# Celery логи
docker compose -f docker-compose.prod.yml logs -f celery

# Обидва разом
docker compose -f docker-compose.prod.yml logs -f web celery
```

### Перевірка міграцій
```bash
# Всі міграції
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations

# Тільки news app
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations news

# Тільки незастосовані
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations | grep "\[ \]"
```

### Перезапуск конкретного сервісу
```bash
# Перезапустити тільки web
docker compose -f docker-compose.prod.yml restart web

# Перезапустити тільки celery
docker compose -f docker-compose.prod.yml restart celery

# Перезапустити все
docker compose -f docker-compose.prod.yml restart
```

### Django shell для тестування
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
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
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml up -d
```

### Проблема 2: Міграції не застосовуються
```bash
# Перевірте чи контейнер запущений
docker compose -f docker-compose.prod.yml ps | grep web

# Перезапустіть контейнер
docker compose -f docker-compose.prod.yml restart web
sleep 10
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Проблема 3: Port already in use
```bash
# Знайдіть процес
sudo lsof -i :8000

# Або зупиніть все
docker compose -f docker-compose.prod.yml down
docker stop $(docker ps -aq)
docker compose -f docker-compose.prod.yml up -d
```

### Проблема 4: Build fails
```bash
# Очистіть кеш Docker
docker system prune -a
docker compose -f docker-compose.prod.yml build --no-cache web celery
```

### Проблема 5: pydyf ImportError або PDF не генерується
```bash
# Встановіть pydyf
docker compose -f docker-compose.prod.yml exec web pip install --no-cache-dir "pydyf==0.10.0"
docker compose -f docker-compose.prod.yml restart web
```

### Проблема 6: hr_contract migration conflict
```bash
# Fake-apply якщо колонка вже існує
docker compose -f docker-compose.prod.yml exec web python manage.py migrate hr 0005_contract_contract_number_employee_id_number_and_more --fake
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
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
