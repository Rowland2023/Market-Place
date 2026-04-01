import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store.settings')

app = Celery('store')
# Use Redis as the broker
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()