#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.1
done

sleep 0.5  # FIXME prevents `django.db.utils.OperationalError: FATAL:  the database system is starting up`
echo "PostgreSQL started"

yes y | python manage.py makemigrations && python manage.py migrate
python manage.py collectstatic --noinput

exec gunicorn wsgi -b 0.0.0.0:8000 --workers 3
