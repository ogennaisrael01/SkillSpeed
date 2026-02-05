from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .payments.urls import payment_urlpatterns

routers = DefaultRouter()

from .import views

routers.register(r"category", viewset=views.CategoryViewSet, basename="category")

skill_routers = NestedSimpleRouter(routers, r"category", lookup="category")
skill_routers.register(r'skills', viewset=views.SkillsViewSet, basename="skills")

urlpatterns = [
    path("home/skills/", views.skills_home, name="home"),
    path("skills/", views.skill_search, name="skill_search"),
    path("child/<uuid:child_pk>/skills/<uuid:skill_pk>/enroll", 
         views.EnrollmentViewSet.as_view(http_method_names=["post"]), name="enroll"),
    path("child/<uuid:child_pk>/enrollments/", views.EnrollmentViewSet.as_view(http_method_names=["get"]),
         name="enroll_ments"),
    path("", include(routers.urls)),
    path("", include(skill_routers.urls))
]

urlpatterns.extend(payment_urlpatterns)