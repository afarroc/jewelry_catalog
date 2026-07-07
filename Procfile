web: gunicorn jewelry_catalog.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A jewelry_catalog worker --loglevel=info