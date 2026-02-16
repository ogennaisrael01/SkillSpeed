from .base import *


ALLOWED_HOSTS = ["*"]
DEBUG = env.bool("DEBUG")
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar", "silk",]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware", 
                   "silk.middleware.SilkyMiddleware"]
    SILKY_PYTHON_PROFILER = True
    SILKY_META = True
    SILKY_ANALYZE_QUERIES = True

INTERNAL_IPS = [ "127.0.0.1", "localhost" ]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://localhost:6379/0",
        "TIMEOUT": 300,
        "KEY_PREFIX": "SkillSpeed"
    } 
}

CELERY_BROKER_URL = "redis://localhost:6379/1"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"