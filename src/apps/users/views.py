from rest_framework import status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action

from .serializers import (UserRegistrationSerializer, User, _,
                          UserVerificationSerializer, OneTimePasswordResendSerializer,
                          PasswordResetRequestSerializer, PasswordResetCodeSerializer,
                          PasswordResetUrlSerializer)
from .helpers import (_validate_serializer, _get_user_by_email, _get_code, _verify_account,
                      _get_one_time_code_or_none, _send_email_to_user, _get_reset_token_or_none,
                      save_user_password, _get_reset_code_or_none)
from .models import OneTimePassword
from .services.helpers import create_otp_for_user, create_password_reset_for_user, _generate_url_for_password_reset
from .services.templates_service import genrate_context_for_otp, generate_context_for_password_reset

from django.db import transaction
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.tokens import PasswordResetTokenGenerator

import logging

logger = logging.getLogger(__name__)

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
        return Response({"status": "success", 
                        "detail": _("Registration successfull. verify your account"),
                        "data": { 
                            "email": valid_serializer.validated_data.get("email"),
                            "first_name": valid_serializer.validated_data.get("first_name"),
                            "last_name": valid_serializer.validated_data.get("last_name")
                            }
                        }
                    )

class CodeUrlVerificationViewSet(viewsets.ModelViewSet):
    http_method_names = ["post", "get"]
    serializer_class = UserVerificationSerializer

    def get_permissions(self):
        if self.action == "retrieve":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        valid_serializer = _validate_serializer(serializer)
        email = valid_serializer.validated_data.get("email")
        code = valid_serializer.validated_data.get("code")
        try:
            user = _get_user_by_email(email)
            one_time_code = _get_code(code, user)
            verify_account = _verify_account(user, one_time_code)
            if verify_account.get("success"):
                return Response({"status": "success", "message": "Account Verification Successfully Completed. You can proceed to login"},
                                status=status.HTTP_200_OK)
        except Exception as exc:
            raise ValidationError(_(f"Account verification Failed due the following exceptions: {exc}"))
    
    def get_queryset(self):
        return OneTimePassword.objects.select_related("users")
    
    def list(self, request, *args, **kwargs):
        code = request.query_params.get("code", None)
        if code is None:
            return Response({"status": "invalid", "detail": "Code not provided"}, status=status.HTTP_400_BAD_REQUEST)
        one_time_password_instance = _get_one_time_code_or_none(code)
        if one_time_password_instance is None:
            return Response({"status": "Failed", "detail": "OTP provided is Invalid"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data={"email": one_time_password_instance.user.email, "code": code})
        if serializer.is_valid(raise_exception=True):
            verify = _verify_account(one_time_password_instance.user, one_time_password_instance)
            if verify.get("status"):
                return Response({"status":"success", "detail": "Account Verification Completed Successfully"}, 
                            status=status.HTTP_200_OK)
        return Response({"status": "Failed", "detail": "OTP verification Failed"}, status=status.HTTP_400_BAD_REQUEST)
    
class OneTimePasswordResendView(APIView):
    http_method_names = ["post"]
    serializer_class = OneTimePasswordResendSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        valid_serializer = _validate_serializer(serializer)
        validated_data = valid_serializer.validated_data
        email = validated_data.get("email")
        try:
            user = _get_user_by_email(email)
            code = create_otp_for_user(user)
            context = genrate_context_for_otp(code=code, email=user.email)
            print(context)
            _send_email_to_user(context=context)
            logger.info("code_resend_request", extra={"email": email})       
        except User.DoesNotExist:
            logger.info("email_does_not_exists",
                extra={"email": email},
            )

        except Exception:
            logger.exception("password_reset_failed",
                extra={"email": email, "view": "PasswordResetView",},
            )
        return Response({"status": "success", "detail": "OneTImePassaword Resend Successfully",
                        }, status=status.HTTP_200_OK)

class PasswordResetViewSet(viewsets.ModelViewSet):
    http_method_names = ["post"]
    serializer_class = PasswordResetRequestSerializer

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        valid_serializer = _validate_serializer(serializer)
        email = valid_serializer.get("email")

        try:
            user = _get_user_by_email(email)
            code = create_otp_for_user(user)
            token = create_password_reset_for_user(user)
            url = _generate_url_for_password_reset(token)

            context = generate_context_for_password_reset(code=code, verification_url=url,
                                                            email=user.email, name=user.full_name,)
            _send_email_to_user(context=context)
            logger.info("password_reset_requested", extra={
                                    "user_id": user.pk, "email": user.email,},)

        except User.DoesNotExist:
            logger.info("password_reset_requested_nonexistent_email",
                extra={"email": email},
            )

        except Exception:
            logger.exception("password_reset_failed",
                extra={"email": email, "view": "PasswordResetView",},
            )

        return Response({"status": "success", "detail": {
                    "message": "password reset instructions have been sent to your email."
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(methods=['post'], detail=False, url_path="confirm")
    def password_comfirm(self, request, *args, **kwargs):
        if "token" in request.query_params:
            serializer = PasswordResetUrlSerializer(data=request.data)
            valid_serializer = _validate_serializer(serializer)
            validated_data = valid_serializer.validated_data
            password  = validated_data.get("password")
            token = request.query_params.get("token")
            if token is None:
                return Response({"status": "failed", "detail": {"message": "Invalid request"}}, 
                                status=status.HTTP_400_BAD_REQUEST)
            token = _get_reset_token_or_none(token=token)
            if token is None:
                return Response({"status": "failed", "deatil": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
            user = token.user
            default_token_generator = PasswordResetTokenGenerator()
            if not default_token_generator.check_token(user, token.reset_token):
                return Response({"status": "failed", "detail": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
            save_user_password(user=user, password=password)
            return Response({"status": "success", "detail": "password_reset_confirmed"}, status=status.HTTP_200_OK)
        
        serializer = PasswordResetCodeSerializer(data=request.data)
        valid_serializer = _validate_serializer(serializer)
        validated_data = valid_serializer.validated_data
        password  = validated_data.get("password")
        code = validated_data.get("code")
        code_instance = _get_reset_code_or_none(code)
        if code_instance is None:
            return Response({"status": "failed", "deatil": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
        user = code_instance.user
        try:
            save_user_password(user, password)
        except Exception as exc:
            logger.exception(f"password_reset_failed: {str(exc)}", extra={"email": user.email})
        return Response({"status": "success", "detail": "password_reset_confirmed"}, status=status.HTTP_200_OK)
