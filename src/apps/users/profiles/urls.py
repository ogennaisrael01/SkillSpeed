from django.urls.resolvers import URLResolver
from rest_framework.routers import DefaultRouter

from django.urls import path, include

from . import views

routers = DefaultRouter()

routers.register(r"profile", views.ProfileManagementViewsets, basename="profile")

child_profile_management = views.ChildProfileManagement.as_view({
    "put": "update",
    "patch": "partial_update",
    "get": "retrieve",
})

interest_create = views.InterestViewSet.as_view({
    "post": "create",
})
interest_detail = views.InterestViewSet.as_view({
    "put": "update",
    "patch": "partial_update",
    "get": "retrieve"
})

certificate_list = views.CertificatedViewSet.as_view({
    "post": "create",
})

certificate_detail = views.CertificatedViewSet.as_view({
    "put": "update",
    "patch": "partial_update",
    "get": "retrieve"
})

profile_urlpatterns: list[URLResolver] = [
    path("profile/detail/", views.ProfileRetrieveAPIView.as_view(), name="auth_user_profile"),
    path("", include(routers.urls)),
    path("account/<uuid:child_pk>/switch/", views.SwithBetweenChildAccountView.as_view(), name="profile_switch"),
    path("child/<uuid:pk>/profile/", child_profile_management, name="child_profile"),
    path("child/<uuid:child_pk>/interest/", interest_create, name="intrest_create"),
    path("child/<uuid:child_pk>/interest/<uuid:pk>/", interest_detail, name="intrest_detail"),
    path("profile/<uuid:instructor_id>/certificate/", certificate_list, name="certificate_list"),
    path("profile/<uuid:instructor_id>/certificate/<uuid:pk>/", certificate_detail, name="certificate_detail"),
]
