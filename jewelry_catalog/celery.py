import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jewelry_catalog.settings')

app = Celery('jewelry_catalog')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
