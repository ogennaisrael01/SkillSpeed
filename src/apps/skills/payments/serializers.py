from rest_framework import serializers

from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils.decorators import method_decorator

from ..helpers import _child_age_or_none, _is_age_appropriate
from .models import Purchase
from .helpers import get_pay_by_tx_ref_or_none, is_payment_pending

import secrets


class PurchaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Purchase
        fields = [
            "price",
            "skill",
            "purchased_by",
            "purchased_for",
            "created_at",
            "purchase_id",
            "purchase_status",
            "tx_ref",
        ]

        read_only_fields = [
            "skill",
            "purchased_by",
            "purchased_for",
            "created_at",
            "purchase_id",
            "purchase_status",
            "tx_ref",
        ]

    default_error_messages = {
        "amount_mismatch": _("The amount does not match the skill price."),
    }

    def validate_price(self, value):
        # Ensure that the amount is the actuall amount for the skill
        skill = self.context.get("skill")
        amount = float(value)
        if amount != skill.price:
            raise self.fail("amount_mismatch")
        return value

    def validate(self, attrs):
        child_profile = self.context.get("child_profile")
        skill = self.context.get("skill")
        request = self.context.get('request')
        if Purchase.objects.filter(
                skill=skill,
                purchased_by=request.user,
                purchased_for=child_profile,
                purchase_status=Purchase.PurchaseStatus.COMPLETED).exists():
            raise serializers.ValidationError(_(
                "This skill has already been purchased for this child profile."
            ),
                                              code="already_purchased")
        if not skill.is_paid:
            raise serializers.ValidationError(
                _("This skill is free and does not require payment."),
                code="free_skill_no_payment")
        child_age = _child_age_or_none(child_profile)
        if child_age is None:
            raise serializers.ValidationError(
                _("Child profile must have a valid date of birth."),
                code="invalid_child_profile")
        if not _is_age_appropriate(skill, child_age):
            raise serializers.ValidationError(
                _("This skill is not appropriate for the child's age."),
                code="age_inappropriate_skill")
        return attrs

    @method_decorator(transaction.atomic)
    def create(self, validated_data):
        child_profile = self.context.get("child_profile")
        skill = self.context.get("skill")
        request = self.context.get("request")
        user = getattr(request, "user")
        if child_profile.guardian != user:
            raise serializers.ValidationError(_(
                "You are not authorized to make a purchase for this child profile."
            ),
                                              code="unauthorized_purchase")
        purchase = Purchase.objects.create(skill=skill,
                                           purchased_by=user,
                                           purchased_for=child_profile,
                                           **validated_data)
        return purchase


class PurchaseVerifySerializer(serializers.Serializer):

    default_error_messages = {
        "pay_not_found":
        _("Payment with the provided transaction reference was not found for the user."
          ),
        "can_verify_only_pending":
        _("Only pending payments can be verified."),
    }

    def validate(self, attrs):
        tx_ref = self.context.get("tx_ref")
        request = self.context.get("request")
        user = getattr(request, "user")
        payment = get_pay_by_tx_ref_or_none(tx_ref=tx_ref, user=user)
        if payment is None:
            self.fail("pay_not_found")
        if not is_payment_pending(payment):
            self.fail("can_verify_only_pending")
        return attrs
