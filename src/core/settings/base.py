from pathlib import Path
import environ
import os

from celery.schedules import crontab

from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(MAIL_ENABLED=(bool, False), SMTP_LOGIN=(str, 'DEFAULT'))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

SENDGRID_API_KEY = env("SENDGRID_API_KEY")
SENDGRID_SENDER = env('SENDGRID_SENDER')

DJANGO_SETTINGS_MODULE =  env("DJANGO_SETTINGS_MODULE", default="core.settings.development")

AUTH_USER_MODEL = "users.CustomUser"

OTP_LIFE = env("OTP_LIFE", default=10)  # in minutes

BASE_URL = env("BASE_URL", default="http://localhost:8000/")
APP_NAME = env("APP_NAME", default="SkillSpeed")

# Application definitionS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    "social_django",
    "drf_yasg",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",

    'apps.users.apps.UsersConfig',
    "apps.skills.apps.SkillsConfig",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

REST_FRAMEWORK = {
    "DEFAULT_AUHTENTICATION_CLASSES": {
        "rest_framework_simplejwt.authentication.JWTAuthentication"
    },
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny"
    ]
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timezone.timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timezone.timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "user_id",
    "USER_ID_CLAIM": "user_id",
}

AUTHENTICATION_BACKENDS = (
    "social_core.backends.github.GithubOAuth2",
    "social_core.backends.google.GoogleOAuth2",
    # "social_core.backends.facebook.FacebookOAuth2",
    "apps.users.backends.CustomBackend"
)


SOCIAL_AUTH_GITHUB_KEY = env("GITHUB_CLIENT_ID")
SOCIAL_AUTH_GITHUB_SECRET = env("GITHUB_CLIENT_SECRET_KEY")
SOCIAL_AUTH_GITHUB_SCOPE = [
    'read:user',
    'user:email',
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("GOOGLE_CLIENT_ID")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("GOOGLE_CLIENT_SECRET_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.profile',
    "https://www.googleapis.com/auth/userinfo.email",
]


LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_LOCATION") + "/0",
        "TIMEOUT": 300,
        "KEY_PREFIX": "SkillSpeed"
    } 
}

CELERY_BROKER_URL = env("REDIS_LOCATION" + "/1", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_LOCATION" + "/1", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
timezone = 'Africa/Lagos'

CELERY_BEAT_SCHEDULE = {
    'auto-expire-otp-every-5-minutes': {
        'task': 'apps.users.services.tasks.auto_expire_otp',
        'schedule': crontab(minute='*/5'),
    },
    "auto-expire-reset-code": {
        "task": "apps.users.services.tasks.auto_deactivate_reset_code",
        "schedule": crontab(minute="*/5")
    }
}
