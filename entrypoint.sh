#!/bin/sh
echo "Running migrations.."
python manage.py makemigrations
python manage.py migrate
python setup_data.py
exec "$@"
