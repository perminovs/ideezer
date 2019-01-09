#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.1
done

sleep 0.5  # FIXME prevents `django.db.utils.OperationalError: FATAL:  the database system is starting up`
echo "PostgreSQL started"

python manage.py migrate django_celery_results

celery -A ideezer worker -l info
