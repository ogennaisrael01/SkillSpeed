from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views

routers = DefaultRouter()
routers.register(r"register", views.RegisterViewSet, basename="register")


urlpatterns = [
    path("", include(routers.urls))
    
]
