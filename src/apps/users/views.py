from rest_framework import status, permissions, viewsets
from rest_framework.response import Response

from .serializers import UserRegistrationSerializer, User, _
from .helpers import _validate_serializer

from django.db import transaction
from django.utils.decorators import method_decorator

class RegisterViewSet(viewsets.ModelViewSet):
    """ A simple view for registring a new user"""
    http_method_names = ["post"]
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        valid_serializer = _validate_serializer(serializer)
        self.perform_create(valid_serializer)
        return Response({"status": "success", "detail": _("Registration successfull. verify your account"),
        "data": { "email": valid_serializer.validated_data.get("email"),
                    "first_name": valid_serializer.validated_data.get("first_name"),
                    "last_name": valid_serializer.validated_data.get("last_name")}})




