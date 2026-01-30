from rest_framework.routers import DefaultRouter

from django.urls import path, include

from . import views

routers = DefaultRouter()

routers.register(r"users", views.ProfileManagementViewsets, basename="profile")

profile_urlpatterns = [
    path("", include(routers.urls))
]