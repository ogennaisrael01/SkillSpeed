from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .auth import CustomObtainPairSerializer, CustomLogoutSerializer
from .helpers import _validate_serializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomObtainPairSerializer

token_obtain_view = CustomTokenObtainPairView.as_view()

class CustomLogoutView(APIView):
    serializer_class = CustomLogoutSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        valid_serializer = _validate_serializer(serializer)
        return Response({"status": "success", "detail": "Logged Out Successfully"} ,status=status.HTTP_200_OK)
    
custom_logout_view = CustomLogoutView.as_view()

