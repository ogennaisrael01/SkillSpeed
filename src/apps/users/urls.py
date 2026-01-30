from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views

routers = DefaultRouter()
routers.register(r"register", views.RegisterViewSet, basename="register")
routers.register(r"verify", views.CodeUrlVerificationViewSet, basename="verify-account")
routers.register(r"password/reset", views.PasswordResetViewSet, basename="password_reset")


urlpatterns = [
    path("", include(routers.urls)),
    path("code/resend/", views.OneTimePasswordResendView.as_view(), name="code_resend")  
]
22