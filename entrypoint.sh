#!/bin/sh
cd testOpenAi/

python manage.py makemigrations --no-input
python manage.py migrate --no-input
python manage.py collectstatic --no-input
python -m spacy download es_core_news_sm --no-input
gunicorn testOpenAi.wsgi:application --bind 0.0.0.0 --timeout 90