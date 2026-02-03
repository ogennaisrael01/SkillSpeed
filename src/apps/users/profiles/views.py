from typing import NoReturn

from rest_framework import viewsets, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.serializers import ListSerializer
from rest_framework.response import Response

from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404
from django.db.models.manager import BaseManager
from django.contrib.auth import get_user_model


from .serializers import (OnboardSerializer, ChildProfileCreateSerializer, 
                          GuardianProfileSerializer, InstructorSerializer, 
                          ChildReadSerializer, InterestSerializer, CertificateSerializer,
                          RoleSwitchSerializer)
from ..helpers import _validate_serializer
from .permissions import (IsGuardian, IsAdminOrInstructor, IsOwner, ChildProfileOwner, 
                          ChildRole, IsInterestOwner, IsInstructor)
from .models import Guardian, Instructor, ChildProfile, ChildInterest, Certificates
from .paginate_profiles import CustomProfilePagination

User = get_user_model()

class ProfileManagementViewsets(viewsets.ModelViewSet):
    http_method_names: list[str] = ["patch", "post", "get"]
    pagination_class = CustomProfilePagination

    def get_serializer_class(self):
        user_role = getattr(self.request.user, "user_role", None)
        if user_role is None:
            raise ValidationError("Account Invalid", code="invalid_profile")
        if user_role == User.UserRoles.INSTRUCTOR:
            return InstructorSerializer
        elif user_role == User.UserRoles.GUARDIAN:
            return GuardianProfileSerializer
        return None
    
    def get_queryset(self) -> BaseManager[Guardian]:
        user_role = getattr(self.request.user, "user_role", None)
        if user_role is None:
            raise ValidationError("Account Invalid", code="invalid_profile")
        if user_role == User.UserRoles.INSTRUCTOR:
            qs = Instructor.objects.select_related("user").prefetch_related("certificates")
            return qs.filter(is_active=True).all()
        elif user_role == User.UserRoles.GUARDIAN:
            qs = Guardian.objects.select_related("user").prefetch_related("children", "children__interest")
            return qs.filter(is_active=True, is_deleted=False).all()
        return None
     
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        if qs is None:
            qs = qs.none()
        else:
            qs = qs.all()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer: NoReturn = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serialzer(qs)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def get_permissions(self):
        if self.action in ("put", "patch"):
            return [IsOwner()]
        if self.action in ("child_onboard", "role_switch"): 
            return [IsGuardian()]
        if self.action in ("list"):
            return [IsAdminOrInstructor()]
        return [permissions.IsAuthenticated()]
    
    @method_decorator(transaction.atomic)
    def partial_update(self, request, *args, **kwargs) -> Response:
        return super().partial_update(request, *args, **kwargs)
    
    @method_decorator(transaction.atomic)
    @action(methods=["patch"], detail=False, url_path="patch")
    def user_profile_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        valid_serialzer = _validate_serializer(serializer=serializer)
        headers = self.get_success_headers(valid_serialzer.validated_data)
        valid_serialzer.save()
        return Response({"status": "success", "detail": valid_serializer.validated_data}, status=status.HTTP_200_OK, headers=headers)
    
    @method_decorator(transaction.atomic)
    @action(methods=["patch"], detail=False, url_path="onboard")
    def onboard(self, request, *args, **kwargs) -> Response:
        serializer = OnboardSerializer(data=request.data, context={'request': request})
        valid_serializer: ListSerializer | transaction.Any | OnboardSerializer = _validate_serializer(serializer=serializer)
        self.perform_create(serializer=valid_serializer)
        return Response({"status": "success", "detail": valid_serializer.data}, status=status.HTTP_200_OK)
    
    @method_decorator(transaction.atomic)
    @action(methods=["post"], detail=False, url_path="child")
    def child_onboard(self, request, *args, **kwargs) -> Response:
        serializer = ChildProfileCreateSerializer(data=request.data, context={"request": request})
        valid_serializer: ListSerializer | transaction.Any | ChildProfileCreateSerializer =  _validate_serializer(serializer=serializer)
    
        self.perform_create(serializer)
        return Response({"status": "success", "deatil": valid_serializer.validated_data}, status=status.HTTP_201_CREATED)
    
    @action(methods=["get"], detail=False, url_path="me")
    def user_profile(self, request, *args, **kwargs) -> Response:
        queryset: BaseManager[Guardian] = self.get_queryset()
        if queryset is None:
            return Response({"status": "error", "detail": "No user profile found"}, status=status.HTTP_404_NOT_FOUND)
        user: transaction.Any | None = getattr(request, "user", None) if hasattr(request, "user") else None
        profile: Guardian = get_object_or_404(queryset, user=user)
        if Guardian.DoesNotExist:
            return Response({"status": "error", "detail": "No user profile found"}, status=status.HTTP_404_NOT_FOUND)
        serializer: NoReturn = self.get_serializer(profile, many=True)
        return Response({"status": "success", "detail": serializer.data}, status=status.HTTP_200_OK)

    @method_decorator(transaction.atomic)
    @action(methods=["patch"], detail=False, url_path="switch")
    def role_switch(self, request, *args, **kwargs):
        serializer = RoleSwitchSerializer(data=request.data, context={"request": request})
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(valid_serializer)
        return Response({"status": "success", "detail": {"user": request.user.email, "active_role": request.user.active_profile}}, 
                        status=status.HTTP_200_OK)

class ChildProfileManagement(viewsets.ModelViewSet):
    http_method_names = ["patch", "put", "get"]
    queryset = ChildProfile.objects.select_related("guardian").prefetch_related("interest")

    def get_serializer_class(self):
        if self.action in ("put", "patch"):
            return ChildProfileCreateSerializer
        return ChildReadSerializer
    
    def get_permissions(self):
        if self.action in ("update", "partial_update"):
            return [ChildProfileOwner()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        return self.queryset.filter(is_active=True, is_deleted=False).all()

    def check_object_permissions(self, request, obj):
        if self.action in ("put", "patch", "destroy"):
            child_id = self.kwargs.get("pk")
            if child_id is None:
                raise ValidationError("child 'pk' is not provided", code="invalid_request")
            child = get_object_or_404(ChildProfile, pk=child_id)
            guardian = getattr(child, "guardian")
            if guardian.user != request.user:
                raise PermissionDenied("You dont have valid access to perform this action", code="invalid_request")
        
class InterestViewSet(viewsets.ModelViewSet):
    serializer_class = InterestSerializer
    queryset = ChildInterest.objects.select_related("child")    
    permission_classes = [ChildRole]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [ChildRole(), IsInterestOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        child = get_object_or_404(ChildProfile, pk=self.kwargs.get("pk"))
        return self.queryset.filter(child=child, is_active=True, is_deleted=False)
    
    def create(self, request, *args, **kwargs):
        child_pk = kwargs.get("child_pk")
        serializer = self.get_serializer(data=request.data, context={"request": request, "child_pk": child_pk})
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(valid_serializer)
        return Response({"status": "success", "detail": valid_serializer.validated_data}, status=status.HTTP_201_CREATED)
    
    def perform_destroy(self, instance):
        if not isinstance(instance, ChildInterest):
            return Response({"status": "failure", "detail": "'instance is not a valid child interest object'"}, 
            status=status.HTTP_400_BAD_REQUEST)
        instance.is_active = False
        instance.is_deleted = True
        instance.save()

class CertificatedViewSet(viewsets.ModelViewSet):
    serializer_class = CertificateSerializer
    queryset = Certificates.objects.select_related("user")
    permission_classes = [IsInstructor]

    def get_queryset(self):
        user_profile = self.request.user.profile if hasattr(self.request.user, "profile") else None
        if user_profile is None:
            return 
        return self.queryset.filter(user=user_profile, is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)

    def create(self, request, *args, **kwargs):
        instructor_profile = kwargs.get("instructor_id")
        profile_instance = get_object_or_404(Instructor, pk=instructor_profile, is_active=True)
        serializer = self.get_serializer(data=request.data, context={"request": request, "instrutor_profile": profile_instance})
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(valid_serializer)
        return Response({"status": "success", "detail": "certificate saved"}, 
                        status=status.HTTP_201_CREATED)
    
