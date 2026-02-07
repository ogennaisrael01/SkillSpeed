from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework import status


from .serializers import RecommendationSerializer, RecommendationReadSerializer
from ...users.profiles.models import ChildProfile
from ...users.profiles.permissions import ChildRole
from .models import Recommendation

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

class RecommendationViewSet(viewsets.ModelViewSet):
    permission_classes  = [ChildRole]
    queryset = Recommendation.objects.select_related("child_profile").prefetch_related("skills")

    def get_serializer_class(self):
        if self.action == "list":
            return RecommendationReadSerializer
        return RecommendationSerializer
    
    def get_queryset(self):
        child_profile = get_object_or_404(ChildProfile, pk=self.kwargs.get("child_pk"), is_active=True)
        if self.request.user.active_account != child_profile:
            raise PermissionDenied()
        return self.queryset.filter(child_profile=child_profile)

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        child_profile = get_object_or_404(ChildProfile, pk=self.kwargs.get("child_pk"), is_active=True)
        if request.user.active_account != child_profile:
            raise PermissionDenied()
        serializer = self.get_serializer(data=request.data, context={"request": request, 'child_profile': child_profile})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
    

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        print(self.get_serializer())
        search = request.query_params.get("search", None)
        queryset = self.filter_queryset(self.get_queryset())
        if search:
            queryset = queryset.filter(Q(skills__name__icontains=search) | 
                                       Q(category__icontains=search) | 
                                       Q(reason__icontains=search) |
                                       Q(difficulty__icontains=search) |
                                       Q(recommenedation_type__icontains=search) |
                                        Q(recommended_by__icontains=search)
                                       ).distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
    