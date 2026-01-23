from __future__ import absolute_import, unicode_literals

from celery import Celery

import os
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "core.settings.base"))

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

@app.task(bind=True)
def debug_tasks(self):
    logger.debug("Request: {0!r}".format(self.request))