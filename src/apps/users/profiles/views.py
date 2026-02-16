
from typing import NoReturn

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.serializers import ListSerializer
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.views import APIView

from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404
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
from .helpers import child_in_guardian_account

User = get_user_model()

class ProfileManagementViewsets(viewsets.ModelViewSet):
    http_method_names: list[str] = ["patch", "get", "post"]
    pagination_class = CustomProfilePagination

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        queryset = None
        if pk:
            guardian_queryset = Guardian.objects.select_for_update("user")\
                .filter(pk=pk, is_active=True, is_deleted=False)
            if guardian_queryset:
                return guardian_queryset
            
            else:
                instructor_queryset = Instructor.objects.select_related("user")\
                            .prefetch_related("certificates")\
                            .filter(pk=pk, is_active=True)
                if instructor_queryset:
                    return instructor_queryset
            
            if instructor_queryset is None or guardian_queryset is None:
                return Response({"status": "failed", "detail": "No profile is associated to this account"}, \
                                status=status.HTTP_404_NOT_FOUND)    

        super_user = getattr(self.request.user, "is_superuser")
        if super_user or self.reqeust.user.user_role == User.UserRoles.INSTRUCTOR:
            guardian = Guardian.objects.select_related("user").filter(is_active=True)
            instructor = Instructor.objects.select_related("user") \
                                .prefetch_related("certificates")\
                                .filter(is_active=True)
            
            return guardian, instructor
        return None
    

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            user_role = getattr(self.request.user, "user_role", None)
            if user_role is None:
                raise ValidationError("Account Invalid", code="invalid_profile")
            if user_role == User.UserRoles.INSTRUCTOR:
                return InstructorSerializer
            elif user_role == User.UserRoles.GUARDIAN:
                return GuardianProfileSerializer
            return None
        
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        queryset  = self.filter_queryset(self.get_queryset())
        if not isinstance(queryset, tuple):
            return Response({"status": "failed", "message": "queryset did not return appropriate data for retrieving user profiles"},\
                            status=status.HTTP_400_BAD_REQUEST)
        guardian, instructor = queryset
        guardian_paginator = self.paginate_queryset(guardian)
        instructor_paginator = self.paginate_queryset(instructor)
        if  guardian_paginator is not None and instructor_paginator is not None:
            guardian_serializer = GuardianProfileSerializer(guardian_paginator, many=True)
            instructor_serialzer = InstructorSerializer(instructor_paginator, many=True)
            return Response({"status": "success", "guardian_data": guardian_serializer.data,\
                             "instructor_data": instructor_serialzer.data}, \
                                status=status.HTTP_200_OK)
        
        guardian_serializer = GuardianProfileSerializer(guardian, many=True)
        instructor_serialzer = InstructorSerializer(instructor, many=True)
    
        return Response({"status": "success", "guardian_data": guardian_serializer.data,\
                             "instructor_data": instructor_serialzer.data}, \
                                status=status.HTTP_200_OK)
        
    def retrieve(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        profile = queryset.first()
        if profile is None:
            return Response({"status": "failed", "detail": "No query found"},\
                            status=status.HTTP_404_NOT_FOUND)
        user_role = getattr(profile.user, "user_role")
        if user_role == User.UserRoles.GUARDIAN:
            serializer = GuardianProfileSerializer(profile)
            return Response({"status": "success", "detail": serializer.data}, status=status.HTTP_200_OK)
        elif user_role == User.UserRoles.INSTRUCTOR:
            serializer = InstructorSerializer(profile)
            return Response({"status": "success", "detail": serializer.data}, status=status.HTTP_200_OK)
        return Response({"status": "failed", "messagae": "invalid profile"}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_permissions(self):
        if self.action in ("put", "patch"):
            return [IsOwner()]
        if self.action in ("child_onboard", "role_switch"): 
            return [IsGuardian()]
        if self.action == "list":
            return [IsAdminOrInstructor()]
        return [permissions.IsAuthenticated()]
    
    @method_decorator(transaction.atomic)
    @action(methods=["post"], detail=False, url_path="onboard")
    def onboard(self, request, *args, **kwargs) -> Response:
        serializer = OnboardSerializer(data=request.data, context={'request': request})
        valid_serializer: ListSerializer | transaction.Any | OnboardSerializer = _validate_serializer(serializer=serializer)
        self.perform_create(serializer=valid_serializer)
        return Response({"status": "success", "detail": valid_serializer.data}, status=status.HTTP_200_OK)
    
    @method_decorator(transaction.atomic)
    @action(methods=["post"], detail=False, url_path="child/onboard")
    def child_onboard(self, request, *args, **kwargs) -> Response:
        serializer = ChildProfileCreateSerializer(data=request.data, context={"request": request})
        valid_serializer =  _validate_serializer(serializer=serializer)
    
        self.perform_create(serializer)
        return Response({"status": "success", "detail": valid_serializer.validated_data}, status=status.HTTP_201_CREATED)
    

    @method_decorator(transaction.atomic)
    @action(methods=["patch"], detail=False, url_path="switch")
    def role_switch(self, request, *args, **kwargs):
        serializer = RoleSwitchSerializer(data=request.data, context={"request": request})
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(valid_serializer)
        return Response({"status": "success", "detail": {"user": request.user.email, "active_role": request.user.active_profile}}, 
                        status=status.HTTP_200_OK)

class ProfileRetrieveAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsOwner]

    def get_object(self):
        user = self.request.user
        user_role = getattr(user, "user_role", None)
        if user_role == User.UserRoles.GUARDIAN:
            try:
                obj = Guardian.objects.get(user=user, is_active=True)
                self.check_object_permissions(self.request, obj=obj)
            except Guardian.DoesNotExist:
                return None
            return obj
        elif user_role == User.UserRoles.INSTRUCTOR:
            try:
                obj = Instructor.objects.get(user=user, is_active=True)
                self.check_object_permissions(self.request, obj)
            except Instructor.DoesNotExist:
                return None
            return obj
        return None


    def get_queryset(self):
        user = self.request.user
        user_role = getattr(user, "user_role", None)
        if user_role == User.UserRoles.INSTRUCTOR:
            return Instructor.objects.select_related("user")\
                .prefetch_related("certificates")\
                .filter(user=user, is_active=True)

        elif user_role == User.UserRoles.GUARDIAN:
            return Guardian.objects.select_related("user")\
                .filter(user=user, is_active=True, is_deleted=False)

        return Instructor.objects.none()

    def get_serializer_class(self):
        user_role = getattr(self.request.user, "user_role", None)
        if user_role is None:
            raise ValidationError("Account Invalid", code="invalid_profile")
        if user_role == User.UserRoles.INSTRUCTOR:
            return InstructorSerializer
        elif user_role == User.UserRoles.GUARDIAN:
            return GuardianProfileSerializer
        return None
    
    def retrieve(self, request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        if queryset is None:
            return Response({"status": "error", "detail": "No user profile found"}, status=status.HTTP_404_NOT_FOUND)
        profile = queryset.first()
        serializer: NoReturn = self.get_serializer(profile)
        return Response({"status": "success", "detail": serializer.data}, status=status.HTTP_200_OK)


class ChildProfileManagement(viewsets.ModelViewSet):
    http_method_names = ["patch", "put", "get"]
    queryset = ChildProfile.objects.select_related("guardian").prefetch_related("interest")

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return ChildProfileCreateSerializer
        return ChildReadSerializer
    
    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [ChildProfileOwner()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        return self.queryset.filter(is_active=True, is_deleted=False).all()
    
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

class SwithBetweenChildAccountView(APIView):
    http_method_names = ["patch"]
    permission_classes = [IsGuardian]
    
    @method_decorator(transaction.atomic)
    def patch(self, request, *args, **kwargs):
        child_pk = kwargs.get("child_pk")
        status, child_profile = child_in_guardian_account(request.user, child_pk)
        if not status:
            raise PermissionDenied("You dont have permission to switch to this child account", code="permission_denied")
        with transaction.atomic():
            request.user.active_account = child_profile
            request.user.save(update_fields=["active_account"])
        return Response({"status": "success", "data": {"child_id": child_profile.pk,
            "name": child_profile.first_name + "  " + child_profile.last_name,
            "guardian": request.user.get_full_name_or_none()
        }})