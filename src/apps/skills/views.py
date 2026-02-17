from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.exceptions import PermissionDenied

from django.db import transaction
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model

from .serializers import (CategorySerializer, SkillCreateSerializer,
                          SkillReadSerializer, EnrollmentSerializer,
                          EnrollmentReadSerializer)
from .models import SkillCategory, Skills, ChildProfile, Enrollment
from ..users.profiles.permissions import IsInstructor, IsOwner, IsGuardian
from ..users.helpers import _validate_serializer
from .paginations import CustomSkillPagination

User = get_user_model()


@api_view(["GET"])
def skills_home(request):
    return Response({"message": "Welcome to the Skills Home!"})


class SkillSearchView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomSkillPagination
    serializer_class = SkillReadSerializer

    def get_queryset(self):
        return Skills.objects.select_related("user", "category").filter(
            is_active=True, is_deleted=False)

    @method_decorator(cache_page(60 * 15))
    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if "search" not in request.query_params:
            qs = qs.order_by("-created_at")
        if qs:
            query = request.query_params.get("search")
            if isinstance(query, str):
                qs = qs.filter(
                    Q(category__name__icontains=query)
                    | Q(name__icontains=query))
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(qs, many=True)
            return Response({
                "status": "success",
                "data": serializer.data
            },
                            status=status.HTTP_200_OK)
        return Response(
            {
                "status": "success",
                "message": "No skills found matching the query"
            },
            status=status.HTTP_404_NOT_FOUND)


skill_search = SkillSearchView.as_view()


class CategoryViewSet(viewsets.ModelViewSet):
    http_method_names = ['post', "patch", "get"]
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SkillCategory.objects.select_related("user")

    def get_queryset(self):
        return self.queryset.filter(is_active=True)

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @method_decorator(transaction.atomic)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class SkillsViewSet(viewsets.ModelViewSet):
    http_method_names = ["post", "get", "delete", "patch"]
    serializer_class = SkillCreateSerializer
    queryset = Skills.objects.select_related("user", "category")
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "category__name", "min_age", "max_age", "name", "price"
    ]
    pagination_class = CustomSkillPagination

    def get_queryset(self):
        qs = self.filter_queryset(self.queryset)
        category_pk = self.kwargs.get("category_pk")
        if "query" in self.request.query_params:
            query = self.request.query_param.get("query")
            qs = qs.filter(Q(category__name__iexact=query.upper())
                           | Q(name__icontains=query)
                           | Q(skill_difficulty__exact=query)
                           | Q(min_age__gte=query) | Q(max_age__lte=query),
                           is_active=True,
                           is_deleted=False)
            return qs
        else:
            qs = qs.filter(category__pk=category_pk,
                           is_active=True,
                           is_deleted=False)
            return qs

    def get_permissions(self):
        if self.action in ("create"):
            return [IsInstructor()]
        if self.action == "partial_update":
            return [IsOwner()]
        return [permissions.IsAuthenticated()]

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        category_pk = kwargs.get("category_pk")
        if category_pk is None:
            return Response(
                {
                    "status": "success",
                    "message": "category pk is not provided"
                },
                status=status.HTTP_400_BAD_REQUEST)

        category_instance = get_object_or_404(SkillCategory,
                                              pk=category_pk.strip(),
                                              is_active=True)
        serializer = self.get_serializer(data=request.data,
                                         context={
                                             "request": request,
                                             "category": category_instance
                                         })
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(valid_serializer)
        return Response(
            {
                "status": "success",
                "message": "Skill added successfully",
                "detail": {
                    "user": request.user.email,
                    "category": category_instance.py
                }
            },
            status=status.HTTP_201_CREATED)


class EnrollmentViewSet(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Enrollment.objects.select_related("child_profile", "skill")
    pagination_class = CustomSkillPagination

    def get_queryset(self):
        child_pk = self.kwargs.get("child_pk")
        qs = self.filter_queryset(self.queryset)
        if qs is None:
            return Response(
                {
                    "status": "failed",
                    "message": "No query set found for your request"
                },
                status=status.HTTP_404_NOT_FOUND)

        filtered_qs = qs.filter(child_profile__pk=child_pk, is_active=True)
        return filtered_qs

    def check_object_permissions(self, request, obj):
        if request.user.active_profile != getattr(User.ActiveProfile, "CHILD"):
            raise PermissionDenied("You cannot perform this request!")
        super().check_object_permissions(request, obj)

    def create(self, request, *args, **kwargs):
        child_pk = kwargs.get("child_pk")
        skill_pk = kwargs.get("skill_pk")
        if child_pk is None or skill_pk is None:
            return Response(
                {
                    "status":
                    "succcess",
                    "message":
                    "child and skill is required before we continue with enrollment"
                },
                status=status.HTTP_400_BAD_REQUEST)
        child_profile = get_object_or_404(ChildProfile,
                                          pk=child_pk,
                                          is_active=True)
        skill = get_object_or_404(Skills, pk=skill_pk, is_active=True)
        serializer = EnrollmentSerializer(data=request.data,
                                          context={
                                              "request": request,
                                              "profile": child_profile,
                                              "skill": skill
                                          })
        valid_serializer = _validate_serializer(serializer)
        self.perform_create(valid_serializer)
        return Response(
            {
                "status": "success",
                "detail": "enrollment successfull",
                "data": {
                    "skill_name": skill.name
                }
            },
            status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if "search" in request.query_params:
            query_param = request.query_params.get("search")
        if query_param is not None:
            qs = qs.filter(skill__name__icontains=query_param, is_active=True)
        page = self.paginate_queryset(queryset=qs)
        if page is not None:
            serializer = EnrollmentReadSerializer(page, many=True)
            return self.get_paginated_response(data=serializer.data)
        serializer = EnrollmentReadSerializer(qs, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        },
                        status=status.HTTP_200_OK)
