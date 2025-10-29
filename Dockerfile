FROM python:3.11-slim

# Системні залежності
# Системні залежності (додано для WeasyPrint + шрифти)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    git \
    libcairo2 \
    pango1.0-tools \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
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
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "300", "lazysoft.wsgi:application"]
