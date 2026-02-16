from .base import *

import dj_database_url

DEBUG = env.bool("DEBUG")

DATABASES = {
    "default": dj_database_url.config(
        default=env("DATABASE_URL"),
        ssl_require=True
        )
}

ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")

CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")