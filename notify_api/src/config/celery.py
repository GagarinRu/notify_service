import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY__")

app.conf.task_queues = {
    "notify": {
        "exchange": "notify",
        "routing_key": "notify",
    }
}
app.conf.task_default_queue = "notify"
app.conf.task_default_exchange = "notify"
app.conf.task_default_routing_key = "notify"

app.autodiscover_tasks()
