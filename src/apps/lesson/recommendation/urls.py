from django.urls import path

from . import views

recommendation_view= views.RecommendationViewSet.as_view({
    "post": "create",
    "get": "list"
})

recommendation_urlpatterns = [
    path("child/<uuid:child_pk>/recommendations/", recommendation_view, name="recommendation")
]