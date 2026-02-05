from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .helpers import create_guadian_profile, create_instructor_profile
from .models import ChildProfile, ChildInterest, Guardian, Instructor, Certificates
from ..serializers import UserReadSerializer

import datetime
User = get_user_model()

class OnboardSerializer(serializers.Serializer):
    required_roles = User.UserRoles

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
                user.user_role = role
                user.save(update_fields=['user_role'])
                if role == User.UserRoles.GUARDIAN:
                    create_guadian_profile(user=user)
                elif role == User.UserRoles.INSTRUCTOR:
                    create_instructor_profile(user=user)
                else:
                    raise serializers.ValidationError(_("role not allowed"), code="invalid_role")
        return validated_data

class InterestSerializer(serializers.ModelSerializer):

    default_error_messages = {
        "user_invalid": _("invalid request, user not founf"),
        "access_denied": _("You cannot perform this action")
    }
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
    def create(self, validated_data):
        user = self.context["request"].user 
        if user is None:
            self.fail("user_invalid")
        child_pk = self.context.get("child_pk")
        child_instance = get_object_or_404(ChildProfile, pk=child_pk)
        if child_instance.guardian != getattr(user, "guardian"):
            self.fail("access_denied")
        with transaction.atomic():
            ChildInterest.objects.create(child=child_instance, **validated_data)
        return validated_data

class ChildProfileCreateSerializer(serializers.ModelSerializer):

    default_error_messages = {
            "invalid_date_of_birth": _("The date_of_birth provided is not valid."),
            "date_of_birth_too_old": _("The child must be less than 15 years old."),
            "date_of_birth_in_future": _("The date_of_birth cannot be in the future."),
            "date_of_birth_required": _("The date_of_birth field is required."),
            "gender_required": _("The gender field is required."),
            "gender_invalid": _("Provided gender is invalid"),
        }
    class Meta:
        model = ChildProfile
        fields = [
            "gender", "date_of_birth",
            "first_name", "last_name",
            "middle_name"
        ]

    def validate_date_of_birth(self, value):
        # max_age: 15 years
        if not value:
            self.fail("date_of_birth_required")
        if not isinstance(value, datetime.date):
            self.fail("invalid_date_of_birth")
        if value > timezone.now().date():
            self.fail("date_of_birth_in_future")
        year = value.year + 15
        if year < timezone.now().date().year:
            self.fail("date_of_birth_too_old")
        return value
    
    def validate_gender(self, value):
        required_genders = ChildProfile.GenderChoices
        if value is None:
            self.fail("gender_required")
        if value.upper() not in required_genders:
            self.fail("gender_invalid")
        return value.upper()
    
    def create(self, validated_data):
        request = self.context.get("request")
        if hasattr(request, "user"):
            user = getattr(request, "user")
        else:
            user = None
        if not user.is_authenticated:
            raise serializers.ValidationError(_("Authentication credentials were not provided"), code="invalid_request")
        user_role = getattr(user, "user_role") if user and hasattr(user, "user_role") else None
        if user_role is None:
            raise serializers.ValidationError(_("Please onboard before you continue"), code="invalid_request")
        if user_role != User.UserRoles.GUARDIAN:
            raise serializers.ValidationError(_("Invalid role"), code="invalid_request")
        fields = ("first_name", "last_name", "middle_name")
        for key in fields:
            validated_data[key] = validated_data[key].title() if validated_data[key] else None
        
        with transaction.atomic():
            ChildProfile.objects.create(guardian=user, **validated_data)
        
        return validated_data
    
class ChildReadSerializer(serializers.ModelSerializer):
    interests = InterestSerializer(many=True, read_only=True)
    guardian = serializers.SerializerMethodField()
    class Meta:
        model = ChildProfile
        fields = [
            "child_id", "gender",
            "date_of_birth", "first_name",
            "last_name", "middle_name",
            "is_active", "created_at",
            "interests", "guardian"
        ]

    def get_guardian(self, obj):
        if not isinstance(obj, ChildProfile):
            return None
        return {
            "guardian_name": obj.guardian.get_full_name_or_none(),
            "email": obj.guardian.email,
            "pk": obj.guardian.pk
        }

class GuardianProfileSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    user = UserReadSerializer(read_only=True)
    class Meta:
        model = Guardian
        fields = [
            "guardian_id", "user",
            "display_name", "is_active",
            "children", "created_at"
        ]
        read_only_fields = [
            "guardian_id", "created_at", 
            "user", "is_active", "children"
        ]

    def get_children(self, obj):
        user = getattr(obj, "user")
        if user is None:
            return []
        children = obj.user.children.all()
        serializer = ChildReadSerializer(children, many=True)
        return serializer.data
    

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class CertificateSerializer(serializers.ModelSerializer):

    default_error_messages = {
        "invalid_date": _("Date object is invalid"),
        "date_in_future": _("Date cannot be in the future"),
        "unauthorized": _("You cannot perform this action")
    }
    class Meta:
        model = Certificates
        fields = [
            "name", "issued_by",
            "issued_on", "description",
            "image", "is_active", 
            "created_at", "certificate_id"
        ]
        read_only_fields = [
            "is_active", "created_at",
            "certificate_id"
        ]
    
    def validate_issued_on(self, value):
        if not isinstance(value, datetime.date):
            self.fail("invalid_date")
        if value > timezone.now().date:
            self.fail("date_in_future")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        instructor_profile = self.context.get("instrutor_profile")
        user_profile = request.user.profile if hasattr(request.user, "profile") else None
        if user_profile is None:
            raise serializers.ValidationError("No Profile for user %s", user_profile)
        if user_profile != instructor_profile:
            self.fail("unauthorized")
        return attrs
    
class InstructorSerializer(serializers.ModelSerializer):
    certificates = CertificateSerializer(required=True)

    default_error_messages = {
        "user_invalid": _("Authentication credentials were not provided")
    }
    class Meta:
        model = Instructor
        fields = [
            "display_name", "certificates"
        ]
    
    def validate_display_name(self, value):
        """
        Docstring for validate_display_name
        
        :param self: Description
        :param value: Return a version of the display name in title case
        """
        return value.title()
    
    def update(self, instance, validated_data):
        request = self.context.get("request")
        user: User = request.user if hasattr(request, "user") else None
        if user is None:
            self.fail("user_invalid")
        display_name = validated_data.get("display_name", instance.display_name)
        if display_name is None:
            display_name = user.get_full_name_or_none()
        certificates = validated_data.get("certificates")
        with transaction.atomic():
            Certificates.objects.create(user=user, **certificates)
            Instructor.objects.update_or_create(user=user, defaults={"display_name": display_name, "is_active": True})

        return validated_data

class RoleSwitchSerializer(serializers.Serializer):
    allowed_roles = getattr(User, "ActiveProfile")
    role = serializers.ChoiceField(choices=allowed_roles, write_only=True)

    default_error_messages = {
        "invalid_role": _("Invalid role provided. request invalid.")
    }
    def validate_role(self, value):
        if value not in self.allowed_roles:
            self.fail("invalid_role")
        return value

    def create(self, validated_data):
        role = validated_data.get("role")
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None:
            raise serializers.ValidationError("Auth credentails not provided!", code="invalid_request")
         
        with transaction.atomic():
            user.active_profile = role.upper() 
            user.save()
        return validated_data