from rest_framework import serializers

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import SkillCategory, Skills, Enrollment
from ..users.serializers import UserReadSerializer
from .payments.models import Purchase

import email_validator

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):

    default_error_messages = {
        "invalid_category": _("The category you provided is invalid. lookout for allowed roles"),
        'category_already_exists': _("Category already exists!")
    }
    class Meta:
        model = SkillCategory
        fields = [
            "category_id", "name",
            "descriptions", "icon",
            "is_active", "created_at"
        ]
        read_only_fields = [
            "is_active", "category_id",
            "created_at"
        ]
    
    def validate_name(self, value):
        allowed_category = getattr(SkillCategory.Category, "choices")
        if value not in allowed_category:
            self.fail("invalid_category")
        if SkillCategory.objects.filter(name=value.upper()).exists():
            self.fail("category_already_exists")
        return value.upper()
    
class SkillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = [
            "name", "description",
            "skill_difficulty", "min_age",
            "max_age", "price", "is_paid"
        ]

    def validate(self, attrs):
        min_age = attrs.get("min_age")
        max_age = attrs.get("max_age")
        if any([min_age, max_age ]) is None:
            raise serializers.ValidationError(_("Please provide the age limit for this skill"), code="provide_age")
        if max_age > 15 or min_age < 5:
            raise serializers.ValidationError(_("'min age' cannot be below 5 and 'max_age' cannot be above 15"))
        name = attrs.get("name")
        attrs["name"] = name.title()
        return attrs
    
    def create(self, validated_data):
        is_paid = validated_data.get("is_paid")
        price = validated_data.get("price")
        if is_paid and price is None or price and not is_paid:
            raise serializers.ValidationError(_("price cannot be empty when is paid is marked true or otherwise"), code='invalid_request')
        request = self.context.get("request")
        category = self.context.get("category")

        if getattr(request.user, "user_role") != User.UserRoles.INSTRUCTOR:
            raise serializers.ValidationError(_("You cannot perform this action"), code="invalid_reuqest")
        if not isinstance(category, SkillCategory):
            raise serializers.ValidationError(_("'category is not a valid skillcategory obj"))
        with transaction.atomic():
            Skills.objects.create(user=request.user, category=category, **validated_data)
        return validated_data
    
class SkillReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    user = UserReadSerializer(read_only=True)
    class Meta:
        model = Skills
        fields = [
            "category", "user",
            "name", "price",
            "description", "min_age",
            "max_age", "is_paid",
            "is_active", "created_at",
            "skill_difficulty"
        ]

class EnrollmentSerializer(serializers.Serializer):
    email = serializers.EmailField()

    default_error_messages = {
        "invalid_email": _("the email you provided is invalid"),
    }

    def validate_email(self, value):
        if value is None:
            raise serializers.ValidationError(_("provide guardian email address used when registring account"), code="invalid_request")
        email = value.strip()
        try:
            email_validator.validate_email(email, check_deliverability=True)
        except email_validator.EmailNotValidError:
            self.fail("invalid_email")
        request = self.context.get("request")
        user = getattr(request, "user")
        if user.email != email:
            raise serializers.ValidationError(_("email mismatch"))
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        skill = self.context.get("skill")
        child_profile = self.context.get("profile")
        user = getattr(request, "user")
        if Enrollment.objects.filter(child_profile=child_profile, skill=skill , is_active=True).exists():
            raise serializers.ValidationError(_('you already enrolled for this skill'))
        if child_profile not in user.children.all():
            raise serializers.ValidationError(_("Invalid request, you cannot perform this action"))
        if skill.is_paid:
            payment = get_object_or_404(Purchase, skill=skill, purchased_by=user, purchased_for=child_profile)
            if payment.purchase_status != Purchase.PurchaseStatus.COMPLETED:
                raise serializers.ValidationError(_("payment is not verified"))
            if payment.price != skill.price:
                raise serializers.ValidationError("payment price doesen't match")
            with transaction.atomic():
                Enrollment.objects.create(skill=skill, child_profile=child_profile)
        with transaction.atomic():
            Enrollment.objects.create(skill=skill, child_profile=child_profile)
        return validated_data
            