from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from .helpers import (_validate_email, _check_email_already_exists, _normalize_and_validate_password)

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
