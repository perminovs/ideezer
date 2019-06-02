#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.1
done

sleep 0.5  # FIXME prevents `django.db.utils.OperationalError: FATAL:  the database system is starting up`
echo "PostgreSQL started"

yes y | python manage.py makemigrations && python manage.py migrate
python manage.py collectstatic --noinput

exec gunicorn wsgi \
      --workers 3 \
      --timeout 60 \
      -b 0.0.0.0:8000 \
      --access-logfile - \
      --error-logfile - \
      --access-logformat "%(h)s %(l)s %(u)s %(t)s pid %(p)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\" %(l)s %(D)s µs"
