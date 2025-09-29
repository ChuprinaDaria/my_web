FROM python:3.11-slim

# Системні залежності
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо requirements та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Копіюємо весь проект
COPY . .

# Створюємо необхідні директорії
RUN mkdir -p logs media staticfiles

# Компілюємо переклади (якщо є)
RUN python manage.py compilemessages --ignore=venv || true

# НЕ запускаємо collectstatic тут - зробимо при старті контейнера
# бо потрібні змінні з .env

EXPOSE 8000

# Entrypoint скрипт
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "lazysoft.wsgi:application"]