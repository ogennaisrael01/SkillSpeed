from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

User = get_user_model()

class OnboardSerializer(serializers.Serializer):
    required_roles = User.UserRoles.choices

    role = serializers.ChoiceField(choices=required_roles, write_only=True, required=True)
    profile_completed  = serializers.BooleanField(required=True)
    default_error_messages = {
        "invalid_role": _("The role provided is not valid."),
    }

    def validate_role(self, value):
        if value not in self.required_roles:
            raise serializers.ValidationError(_("Invalid_request: Role Invalid"), code="invalid_request")
        return value
    
    def create(self, validated_data):
        role = validated_data.get("role")
        profile_completed = validated_data.get("profile_completed")
        if role:
            profile_completed = True
        else:
            profile_completed = False
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None:
            raise serializers.ValidationError(_("Authentication Credentails were not provided"), code="invalid_request")
        active_role = getattr(user, "user_role")
        if active_role is not None:
            raise serializers.ValidationError(_("user already has an active role"), code="user_role_active")
        if profile_completed:
            with transaction.atomic():
                user.role = role
                user.save(update_fields=['role'])
            
        return validated_data

