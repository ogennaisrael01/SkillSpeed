from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views
from .auth_views import token_obtain_view, custom_logout_view
from  .profiles.urls import profile_urlpatterns

routers = DefaultRouter()
routers.register(r"register", views.RegisterViewSet, basename="register")
routers.register(r"verify", views.CodeUrlVerificationViewSet, basename="verify-account")
routers.register(r"password/reset", views.PasswordResetViewSet, basename="password_reset"),


urlpatterns = [
    path("auth/", include(routers.urls)),
    path("auth/code/resend/", views.OneTimePasswordResendView.as_view(), name="code_resend"),
    path("auth/token/obtain/", token_obtain_view, name="login"),
    path("auth/logout/", custom_logout_view, name="logout")
]

# extends profile urls
urlpatterns.extend(profile_urlpatterns)
