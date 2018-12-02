#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.1
done

echo "PostgreSQL started"

python manage.py makemigrations && python manage.py migrate

gunicorn wsgi -b 0.0.0.0:8000 --workers 3
