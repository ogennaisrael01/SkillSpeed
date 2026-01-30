from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import OnboardSerializer
from ..helpers import _validate_serializer

class ProfileManagementViewsets(viewsets.ModelViewSet):
    http_method_names = ["patch"]
    permission_classes = [permissions.AllowAny]
    serializer_class = OnboardSerializer

    @action(methods=["patch"], detail=False, url_path="onboard")
    def onboard(self, request, *args, **kwargs):
        serializer = OnboardSerializer(data=request.data, context={'request': request})
        valid_serializer = _validate_serializer(serializer=serializer)
        self.perform_create(serializer=valid_serializer)
        return Response({"status": "success", "detail": valid_serializer.data}, status=status.HTTP_200_OK)