#!/bin/bash
set -e

echo "Waiting for postgres..."
until python -c "import socket; s = socket.socket(); s.connect(('$DB_HOST', int('$DB_PORT'))); s.close()" 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL started"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting application..."
exec "$@"