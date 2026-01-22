from .base import *

DEBUG = env.bool("DEBUG")

DATABASES = {
    "default": {
        "ENGINE": env("POSTGRES_ENGINE"),
        "NAME": env("POSTGRES_NAME"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env.int("POSTGRES_PORT")
    }
}

ALLOWED_HOSTS = env("ALOOWED_HOSTS").split(",")

CELERY_BROKER_URL = env("REDIS_LOCATION") + "/1"
CELERY_RESULT_BACKEND = env("REDIS_LOCATION") + "/1"