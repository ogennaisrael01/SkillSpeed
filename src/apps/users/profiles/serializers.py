from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.db.models import DateField

from .helpers import create_guadian_profile, create_instructor_profile
from .models import ChildProfile, ChildInterest

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
                if role == User.UserRoles.GUARDIAN:
                    create_guadian_profile(user=user)
                elif role == User.UserRoles.INSTRUCTOR:
                    create_instructor_profile(user=user)
                else:
                    raise serializers.ValidationError(_("role not allowed"), code="invalid_role")
        return validated_data

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildInterest
        fields = [
            "name", "description",
            "is_active", "created_at",
            "interest_id"
        ]
        read_only_fields = [
            "is_active", 'created_at',
            "interest_id"
        ]

class ChildProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildProfile
        fields = [
            "gender", "date_of_birth",
            "first_name", "last_name",
            "middle_name"
        ]

        default_error_messages = {
            "invalid_date_of_birth": _("The date_of_birth provided is not valid."),
            "date_of_birth_too_old": _("The child must be  less than 15 years old."),
            "date_of_birth_in_future": _("The date_of_birth cannot be in the future."),
            "date_of_birth_required": _("The date_of_birth field is required."),
            "gender_required": _("The gender field is required."),

        }
    def validate_date_of_birth(self, value):
        # max_age: 15 years
        if not value:
            raise serializers.ValidationError(self.error_messages["date_of_birth_required"], code="date_required")
        if not isinstance(value, DateField):
            raise serializers.ValidationError(self.error_messages["invalid_date_of_birth"], code="invalid_date_of_birth")
        if value > timezone.now().date():
            raise serializers.ValidationError(self.error_messages["date_of_birth_in_future"], code="invalid_date_of_birth")
        year = value.year + 15
        if year < timezone.now().date().year:
            raise serializers.ValidationError(self.error_messages["date_of_birth_too_old"], code="invalid_date_of_birth")
        return value
    
    def validate_gender(self, value):
        pass
        