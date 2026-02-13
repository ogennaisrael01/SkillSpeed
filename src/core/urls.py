from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from .drf_yasg import get_swagger_view
from .service import health_check, test_send_email

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/sk/", include("apps.skills.urls")),
    path("api/v1/sk/", include("apps.lesson.urls")),
    path("health/", health_check, name="health"),
    path("email/", test_send_email, name="email"),
]

urlpatterns += [
    path("docs/", get_swagger_view().with_ui("swagger", cache_timeout=10), name="api_docs"),
    path("redocs/", get_swagger_view().with_ui("redoc", cache_timeout=10), name="api_redocs")
]

DEBUG = getattr(settings, "DEBUG", None)
DJANGO_ENV = getattr(settings, "DJANGO_SETTINGS_MODULE")

if DEBUG and DJANGO_ENV != "core.settings.production":
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
    urlpatterns += [path('silk', include('silk.urls', namespace='silk'))]
