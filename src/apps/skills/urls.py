from django.urls import path, include

from .import views
urlpatterns = [
    path("home/skills/", views.skills_home, name="home")
]