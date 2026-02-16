from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from .helpers import (_validate_email, _check_email_already_exists, _normalize_and_validate_password,
                      _get_user_by_email, _get_code, _get_reset_code_or_none)
from .services.helpers import _hash_otp_code

import email_validator
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(max_length=200, 
                            write_only=True, error_messages={"required": _("provide confirm password")})
    class Meta:
        model = User
        fields = [
            "email", "first_name",
            "last_name", "password",
            "confirm_password"
        ]
        extra_kwargs = {
                "password": {
                    "write_only": True
                    }
                }
    
    def validate(self, attrs: dict) -> dict:
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        if password != confirm_password:
            raise serializers.ValidationError(_("Password mismatch. Please provide a matching password"))
        for field in ("first_name", "last_name"):
            value = attrs.get(field)
            if not attrs[field] or value is None:
                raise serializers.ValidationError(_(f"{value} cannot be empty..."))
            attrs[field] = value.title() 
        return attrs

    def validate_email(self, value: str):
        email = value.strip()
        valid_email = _validate_email(email)
        if not valid_email.get("success"):
            raise email_validator.EmailNotValidError()
        user = _check_email_already_exists(valid_email.get("valid_email"))
        if user:
            raise serializers.ValidationError(_(f"user with {user} already exists"))
        return valid_email.get("valid_email")
    
    def validate_password(self, value):
        _normalize_and_validate_password(value)
        return value
    
    def validate_confirm_password(self, value):
        _normalize_and_validate_password(value)
        return value
    
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        try:
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)
            logger.info("A new user instance is created %s", user.email)
            return user
        except Exception:
            raise

class UserVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)

    def validate_email(self, value):
        if _validate_email(value).get("success"):
            return _validate_email(value).get("valid_email")

    def validate_code(self, value):
        if not isinstance(value, str):
            raise serializers.ValidationError(_("%s is not a valid str instance", value))
        return value
    
    def validate(self, attrs):
        email, code = attrs.get("email"), attrs.get("code")
        if email is None or code is None:
            raise serializers.ValidationError(_("'email' or code is required to valaidate account"))
        if _check_email_already_exists(email):
            raise serializers.ValidationError("Account already verified and ready for login")
        
        user = _get_user_by_email(email)
        if not user.account_status == User.AccountStatus.ACTIVE:
            raise serializers.ValidationError("Account already deactivated")
        
        one_time_password = _get_code(code, user)
        if user is None or one_time_password is None:
            raise serializers.ValidationError(_("Invalid code or email provided"))
        
        if not one_time_password.is_active or one_time_password.is_used:
            raise serializers.ValidationError("Password already expired or used. Request another one")
        return attrs

class OneTimePasswordResendSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, required=True)

    def validate_email(self, value):
        valid_email = _validate_email(value.strip())
        user = _get_user_by_email(valid_email.get("valid_email"))
        if user is None:
            raise serializers.ValidationError(_("Invalid credentials provided"), code="invalid_email_address")
        
        return valid_email.get("valid_email")
    
class PasswordResetRequestSerializer(OneTimePasswordResendSerializer):
    pass

class PasswordResetCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=100, write_only=True, required=True)
    password = serializers.CharField(max_length=100, write_only=True, required=True)
    confirm_password = serializers.CharField(max_length=100, write_only=True, required=True)

    def validate(self, attrs: dict) -> dict:
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        if password != confirm_password:
            raise serializers.ValidationError(_("Password mismatch. Please provide a matching password"))
        return attrs
    def validate_password(self, value):
        password_validate = UserRegistrationSerializer()
        return password_validate.validate_password(value)
    
    def validate_confirm_password(self, value):
        confirm_password_validate = UserRegistrationSerializer()
        return confirm_password_validate.validate_confirm_password(value)
    
    def validate_code(self, value):
        code = value.strip()
        code_instance = _get_reset_code_or_none(code)
        if code_instance is None:
            raise serializers.ValidationError("Invalid code provided", code="invalid_request")
        if code_instance.user is None:
            raise serializers.ValidationError("Invalid", code="user_invalid")
        return value
    
class PasswordResetUrlSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=100, write_only=True, required=True)
    confirm_password = serializers.CharField(max_length=100, write_only=True, required=True)

    def validate(self, attrs: dict) -> dict:
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        if password != confirm_password:
            raise serializers.ValidationError(_("Password mismatch. Please provide a matching password"))
        return attrs
    def validate_password(self, value):
        password_validate = UserRegistrationSerializer()
        return password_validate.validate_password(value)
    
    def validate_confirm_password(self, value):
        confirm_password_validate = UserRegistrationSerializer()
        return confirm_password_validate.validate_confirm_password(value)


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email", "first_name",
            "last_name", "user_role",
            "is_active", "account_status",
            
        ]
