from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from .helpers import _validate_email, user_can_authenticate

User = get_user_model()

class CustomObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        password = attrs.get("password")
        email = _validate_email(attrs["email"])
        valid_email = email["valid_email"] if email.get("succes") else None
        try:
            user = User.objects.get(email=valid_email) 
        except User.DoesNotExist:
            raise AuthenticationFailed(code="invalid_credentials", detail={"status": "Failed"})
        if not user_can_authenticate(user=user):
            raise AuthenticationFailed(code="invalid_request", detail={"status": "Failed", "detail": "account not verified"})
        if not user.check_password(password):
            raise AuthenticationFailed(code="invalid_credentails", detail={"status": "failed", "detail": "invalid_credentials"})
        self.user = user
        data.update({"user_data": {
            "user_id": user.pk, "email": user.email,
            "name": user.get_full_name_or_none() if user.get_full_name_or_none() else None
        }})
        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token.verify()
        token.set_jti()
        token["email"] = getattr(user, "email", None)
        return token
    
class CustomLogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True, write_only=True, error_messages={
        "required": _("Refresh token is required to logout.")
    })
    default_error_messages = {
        "bad_token": _("Token is invalid or expired")
    }

    def get_user_from_token(token: str):
        token = RefreshToken(token=token)
        return token.get("user_id")
    
    def validate(self, attrs):
        data = super().validate(attrs)
        request = self.context.get("request")
        user = request.user 
        if user is None or "Anonymous": 
            raise serializers.ValidationError(_("Authentication credentials were not provided"), code="invali_request")
        token = attrs.get("refresh_token")
        user_id = self.get_user_from_token(token)
        if user_id != user.pk:
            raise serializers.ValidationError(_("Invalid Request. refresh token is Invalid"), code="refresh_token_invalid")
        with transaction.atomic():
            outstanding_tokens = OutstandingToken.objects.filter(user=user).all()
            # black list all outstanding token for this user
            BlacklistedToken.objects.bulk_create(
                BlacklistedToken(token=token) for token in outstanding_tokens
            )
        return attrs