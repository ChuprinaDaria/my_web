# 🚀 Інструкції для деплою змін

## Зміни в цьому релізі:

1. ✅ Виправлено NewsCategory migrations (видалено cta_link)
2. ✅ Виправлено блокування Google ботів (reverse DNS verification)
3. ✅ Додано empty migrations для hr та rag

---

## 📋 Команди для деплою на сервері

### 1. Зупинити контейнери
```bash
cd /opt/lazysoft
docker-compose down
```

### 2. Отримати останні зміни з Git
```bash
git fetch origin
git checkout claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt
git pull origin claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt
```

### 3. Перебудувати контейнери (важливо!)
```bash
docker-compose build --no-cache web celery
```

### 4. Запустити контейнери
```bash
docker-compose up -d
```

### 5. Застосувати міграції
```bash
# Міграції для hr app
docker-compose exec web python manage.py migrate hr

# Міграції для rag app
docker-compose exec web python manage.py migrate rag

# Міграції для news app
docker-compose exec web python manage.py migrate news

# Або всі разом
docker-compose exec web python manage.py migrate
```

### 6. Перевірити що все працює
```bash
# Перевірити статус контейнерів
docker-compose ps

# Перевірити логи web
docker-compose logs -f --tail=100 web

# Перевірити логи celery (в окремому терміналі)
docker-compose logs -f --tail=100 celery

# Перевірити що немає помилок міграцій
docker-compose exec web python manage.py showmigrations
```

### 7. Перевірити Google Bot fix
```bash
# Через 10-15 хвилин перевірте логи
tail -f /opt/lazysoft/logs/security.log

# Перевірте що немає fake_bot для Google IP
grep "fake_bot" /opt/lazysoft/logs/security.log | grep -E "(192.178|2001:4860)" | tail -20

# Якщо порожньо - все ОК! ✅
```

---

## 🔥 Швидкий деплой (одна команда)

Скопіюйте і виконайте все разом:

```bash
cd /opt/lazysoft && \
git fetch origin && \
git checkout claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt && \
git pull origin claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt && \
docker-compose down && \
docker-compose build --no-cache web celery && \
docker-compose up -d && \
sleep 10 && \
docker-compose exec web python manage.py migrate && \
docker-compose logs --tail=50 web celery
```

---

## ⚠️ Можливі проблеми та рішення

### Проблема 1: `docker-compose: command not found`
```bash
# Встановіть docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Проблема 2: Міграції не застосовуються
```bash
# Перевірте чи контейнер запущений
docker-compose ps

# Якщо web не запущений
docker-compose up -d web

# Подивіться логи помилок
docker-compose logs web | grep -i error
```

### Проблема 3: Порт вже зайнятий
```bash
# Знайдіть процес який використовує порт
sudo lsof -i :8000

# Вбийте процес
sudo kill -9 <PID>

# Або зупиніть всі контейнери
docker-compose down
docker stop $(docker ps -aq)
```

### Проблема 4: NewsCategory errors продовжуються
```bash
# Перевірте чи міграції застосувались
docker-compose exec web python manage.py showmigrations news | grep "0016_remove_newscategory_cta_link"

# Якщо не застосована, застосуйте вручну
docker-compose exec web python manage.py migrate news 0016_remove_newscategory_cta_link
docker-compose exec web python manage.py migrate news
```

---

## 📊 Перевірка після деплою

### 1. Перевірка міграцій ✅
```bash
docker-compose exec web python manage.py showmigrations | grep "\[ \]"
# Має бути порожньо (всі міграції застосовані)
```

### 2. Перевірка AI процесора ✅
```bash
docker-compose logs celery | grep -i "newsсategory\|fielderror" | tail -20
# Не має бути помилок NewsCategory
```

### 3. Перевірка Google Bot ✅
```bash
# Через 30 хвилин після деплою
grep "fake_bot" /opt/lazysoft/logs/security.log | tail -20
# Не має бути Google IP (192.178.*, 2001:4860:*)
```

### 4. Перевірка сайту ✅
```bash
curl -I https://lazysoft.pl
# Має повернути 200 OK

curl https://lazysoft.pl/sitemap.xml
# Має повернути XML sitemap
```

---

## 🎯 Очікувані результати

✅ Контейнери запущені без помилок
✅ Міграції hr, rag, news застосовані
✅ AI процесор працює без NewsCategory errors
✅ Google боти не блокуються
✅ Сайт доступний і працює

---

**Створено**: 2025-10-30
**Branch**: `claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt`
**Автор**: Claude Code
