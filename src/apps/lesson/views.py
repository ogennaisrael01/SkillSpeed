from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import permissions, viewsets, status
from rest_framework.exceptions import PermissionDenied

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q

from .serializers import (LessonCreateSerializer, LessonReadSerializer, 
                          ProjectSerializer, SubmissionCreateSerializer,
                          FeebBackSerializer, AcceptRejectProjectSerializer,
                          SubmissionReadSerializer)
from .models import LessonContent, Skills, Projects, Submission
from ..users.profiles.permissions import ChildRole, IsAdminOrInstructor
from ..skills.models import Enrollment
from ..users.helpers import _validate_serializer
from .helpers import (can_access_content, user_current_level, _get_contents_for_user, 
                      get_current_status, create_progress_record, get_content_by_pk, 
                      get_project_by_pk, can_create_content)
from .paginate import CustomLessonPagination

@api_view(http_method_names=["get"])
def lesson(request) -> Response:
    return Response({"status": "success", "message": "Lesson API is working!"})

class LessonContentViewSet(viewsets.ModelViewSet):
    serializer_class = LessonCreateSerializer
    queryset = LessonContent.objects.select_related("skill", "skill__user")
    pagination_class = CustomLessonPagination 

    def get_serializer_class(self):
        if self.request.method == ['get']:
            return LessonReadSerializer
        return LessonCreateSerializer
    
    def get_queryset(self):
        skill_pk = self.kwargs.get("skill_pk")
        qs = self.filter_queryset(self.queryset)
        if skill_pk is None or qs is None:
            qs = qs.none()
        else:
            qs = qs.filter(skill__pk=skill_pk, is_active=True, is_published=True)
        return qs
        
    def get_permissions(self):
        if self.action in ("create", "put", "partial_update", "destroy"):
            return [IsAdminOrInstructor()]
        return [ChildRole()]
    
    def check_object_permissions(self, request, obj):
        if request.method == ['get', "post"]:
            skill_pk = self.kwargs.get("skill_pk")
            if not can_access_content(request, skill_pk):
                raise PermissionDenied()
        super().check_object_permissions(request, obj)
    
    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        skill_pk = kwargs.get("skill_pk")
        skill_instance = get_object_or_404(Skills, pk=skill_pk, is_active=True)
        serializer = self.get_serializer(data=request.data, 
                                         context={"request": request, "skill": skill_instance})
        
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(valid_serializer)
        return Response({"status": "success", "detail": {"message": "skill content added successfully", 
                                                         "data": valid_serializer.validated_data}}, 
                                                         status=status.HTTP_201_CREATED)
    
    @method_decorator(transaction.atomic)
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_update(valid_serializer)
        return Response({"status": "success", "detail": {"message": "skill content updated successfully", 
                                                         "data": valid_serializer.validated_data}}, 
                                                         status=status.HTTP_201_CREATED)

    
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(transaction.atomic)
    def perform_destroy(self, instance):
        if not isinstance(instance, LessonContent):
            return None
        instance.deactivate()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

    def retrieve(self, request, *args, **kwargs):
        content_obj = self.get_object()
        if not content_obj.is_active:
            return Response({"status": "error", "message": "This content is not verified"})
        user_level = user_current_level(request, getattr(content_obj.skill, "pk"))
        if user_level != content_obj.content_order:
            return Response({"status": "error", 
                             "detail": {"message": "You have not unlocked this content yet. Please complete previous contents to unlock it."}},
                             status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(content_obj)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    @method_decorator(transaction.atomic)
    @action(methods=["post"],  detail=True)
    def mark_as_completed(self, request, *args, **kwargs):
        content = self.get_object()
        child_profile = getattr(request.user, "active_account")
        enrollment = getattr(child_profile, "enrollment")
        if not isinstance(enrollment, Enrollment):
            return Response({"status": "error", "detail": {"message": "You are not enrolled in this skill. Please enroll to access this content."}}, 
                            status=status.HTTP_403_FORBIDDEN)
        if enrollment.skill.pk != content.skill.pk:
            return Response({"status": "error", "detail": {"message": "This content does not belong to the skill you are enrolled in."}}, 
                            status=status.HTTP_403_FORBIDDEN)
        current_content_status = get_current_status(content)
        if current_content_status != LessonContent.ContentStatus.IN_PROGRESS:
            return Response({"status": "success", "detail": "This content has already been completed, you can continue with the next content"}, 
                            status=status.HTTP_200_OK)
        try:
            with transaction.atomic():
                content.mark_as_completed()
                create_progress_record(child_profile, content)
        except Exception as e:
            return Response({"status": "error", "detail": {"message": f"An error occurred while marking content as completed: {str(e)}"}}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"status": "success", "detail": {"message": "Content marked as completed successfully."}}, 
                        status=status.HTTP_200_OK)

class ProjectsViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    pagination_class = CustomLessonPagination

    queryset = Projects.objects.select_related("lesson_content")

    def get_permissions(self):
        if self.action in ("create", "put", "partial_update", "destroy"):
            return [IsAdminOrInstructor()]
        return [ChildRole()]
    
    def get_queryset(self):
        content = get_content_by_pk(self.kwargs.get("content_pk"))
        qs = self.filter_queryset(self.queryset)
        if qs:
            qs = qs.filter(lesson_content=content, is_active=True)
            return qs
        return qs.none()
    
    def check_object_permissions(self, request, obj):
        content = get_content_by_pk(self.kwargs.get("content_pk"))
        if request.method == ["get"]:
            if not can_access_content(request, content.skill.pk):
                raise PermissionDenied()
        elif request.method in ("post", "delete", "put", "patch"):
            if not can_create_content(content.skill, request.user):
                raise PermissionDenied()
            
        super().check_object_permissions(request, obj)

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        content = get_content_by_pk(kwargs.get("content_pk"))
        serializer = self.get_serializer(data=request.data, context={"request": request, "content": content })   
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(valid_serializer)
        return Response({"status": "success", "detail": valid_serializer.validated_data}, status=status.HTTP_201_CREATED)

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(transaction.atomic)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    

    def perform_destroy(self, instance):
        with transaction.atomic():
            instance.deactivate()

class SubmissionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    queryset = Submission.objects.select_related("project", "child_profile")
    
    def get_serializer_class(self):
        if self.request.method == ["get"]:
            return SubmissionReadSerializer
        return SubmissionCreateSerializer
    
    def get_queryset(self):
        qs = self.filter_queryset(self.queryset)
        if qs is None:
            qs = qs.none()
        else:
            qs = qs.filter(Q(child_profile=self.request.user.active_account) |
                       Q(project__lesson_content__skill__user=self.reqeust.user))
        return qs
    
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if qs is None:
            return Response({"status": "not_found", "message": "no response for your request"}, 
                            status=status.HTTP_404_NOT_FOUND)
        project_pk = kwargs.get("project_pk")
        qs = qs.filter(project__pk=project_pk)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
    
    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        project_pk = kwargs.get("project_pk")
        project = get_project_by_pk(project_pk)
        serializer = self.get_serializer(data=request.data, context={"project": project})
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(valid_serializer)
        return Response({"status": "success", "detail": valid_serializer.validated_data}, 
                        status=status.HTTP_201_CREATED)
    
    @method_decorator(transaction.atomic)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 15))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    
    @method_decorator(cache_page(60 * 15))
    @action(methods=["get"], detail=False, url_path="submissions")
    def submissions(self, request, *args, **kwargs):
        query = request.query_params.get("status")
        qs = self.get_queryset()
        if query is None:
            qs = qs
        else:
            qs = qs.filter(status__icontains=query)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Respone({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
    
    @method_decorator(transaction.atomic)
    @action(methods=["patch"], detail=True, url_path="feedback")
    def feedback(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = FeebBackSerializer(instance, data=request.data, partial=True)
        valid_serialzier = _validate_serializer(serializer)
        self.perform_update(serializer=valid_serialzier)
        return Response({"status": "success", "data": valid_serializer.data}, status=status.HTTP_200_OK)
    
    @method_decorator(transaction.atomic)
    @action(methods=['patch'], detail=True)
    def approve_reject_project(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AcceptRejectProjectSerializer(instance, data=request.data, partial=True)
        valid_serializer = _validate_serializer(serializer)
        self.perform_update(valid_serialzer)
        return Response({"status": "success", "data": valid_serializer.data}, status=HTTP_200_OK)
    


