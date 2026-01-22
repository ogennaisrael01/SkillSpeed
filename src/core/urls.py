from django.contrib import admin
from django.urls import path, include
from django.conf import settings 

from .service import health_check, test_send_email


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/vi/auth/", include("apps.users.urls")),
    path("health/", health_check, name="health"),
    path("email/", test_send_email, name="email"),
    path('', include('social_django.urls', namespace='social')),
]

DEBUG = getattr(settings, "DEBUG", None)
DJANGO_ENV = getattr(settings, "DJANGO_SETTINGS_MODULE")

if DEBUG and DJANGO_ENV != "core.settings.production":
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
