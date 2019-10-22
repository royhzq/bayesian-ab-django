#!/bin/sh
echo "Running migrations.."
# python manage.py makemigrations
# python manage.py migrate
python manage.py test
python setup_data.py
exec "$@"
