#!/bin/sh
echo "Running migrations.."
python manage.py makemigrations
python manage.py migrate
exec "$@"
