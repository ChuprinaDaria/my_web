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
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проект
COPY . .

# Створюємо необхідні директорії
RUN mkdir -p logs media staticfiles

# Збираємо статику
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Команда запуску
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "lazysoft.wsgi:application"]