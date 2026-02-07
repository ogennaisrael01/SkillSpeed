from django.urls import path

from . import views
from .recommendation.urls import recommendation_urlpatterns


content_view = views.LessonContentViewSet.as_view({
    "post": "create",
    "get": "list"
}
)

content_detail = views.LessonContentViewSet.as_view({
    "put": "update",
    "get": "retrieve",
    "delete": "destroy",
    "patch": "partial_update"
})

mark_completed = views.LessonContentViewSet.as_view({
    "post": "mark_as_completed"
})

projects_view = views.ProjectsViewSet.as_view({
    "post": "create",
    "get": "list"
})

project_detail = views.ProjectsViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy"
})
submission_view = views.SubmissionViewSet.as_view({
    "post": "create",
    "get": "list"
})
submission_detail = views.SubmissionViewSet.as_view({
    "put": 'update',
    "get": "retrieve",
    "patch": "partial_update"
})
submissions = views.SubmissionViewSet.as_view({
    "get": "submissions",
})
feedback = views.SubmissionViewSet.as_view({
    "patch": "feedback"
})

urlpatterns = [
    path("lesson/", views.lesson, name="lesson"),
    path("skills/<uuid:skill_pk>/contents/", content_view, name="content-view"),
    path("skills/<uuid:skill_pk>/contents/<uuid:pk>/", content_detail, name="content-detail"),
    path("skills/<uuid:skill_pk>/contents/<uuid:pk>/mark/complete/", mark_completed, name="content-detail"),
    path("content/<uuid:content_pk>/projects/", projects_view, name="project_view"),
    path("content/<uuid:content_pk>/projects/<uuid:pk>/", project_detail, name="project_view"),
    path("projects/<uuid:project_pk>/submissions/", submission_view, name="submission_create"),
    path("projects/<uuid:project_pk>/submissions/<uuid:pk>/", submission_detail, name="submission_detail"),
    path("projects/<uuid:project_pk>/submissions/<uuid:pk>/feeback/", feedback, name="feedback"),
    path("projects/submissions/", submissions, name="submissions"),
]


# extend recommendation url 
urlpatterns.extend(recommendation_urlpatterns)