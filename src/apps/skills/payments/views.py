from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from .serializers import PurchaseSerializer, PurchaseVerifySerializer
from ...users.helpers import _validate_serializer
from ...users.profiles.permissions import ChildRole, IsGuardian
from .payments import Payment
from ..models import Skills, ChildProfile
from .permissions import IsPayOwner
from .helpers import (get_pay_by_tx_ref_or_none, completed_purchase, 
                    failed_purchase, verify_payment_amount, is_payment_completed, is_payment_failed)

import secrets

class PaymentView(CreateAPIView):
    serializer_class = PurchaseSerializer
    permission_classes = [IsGuardian]

    def create(self, request, *args, **kwargs):
        skill_pk = kwargs.get("skill_pk")
        child_pk = kwargs.get("child_pk")

        skill_instance = get_object_or_404(Skills, pk=skill_pk, is_active=True, is_deleted=False, is_paid=True)
        child_Profile_instance = get_object_or_404(ChildProfile, pk=child_pk, is_active=True)
        guardian = request.user
        serializer = self.get_serializer(data=request.data, context={
            "request": request,
            "skill":    skill_instance,
            "child_profile": child_Profile_instance
        })
        valid_serializer = _validate_serializer(serializer=serializer)
        data = valid_serializer.validated_data
        amount = data.get("price")
        if amount != skill_instance.price:
            return Response({"status": "success", "message": "Amount mismatch"}, status=400)
        payment = Payment()
        tx_ref = f"payme_{secrets.token_urlsafe(20)}"
        response = payment.initialize_payment(
            email=guardian.email,
            amount=amount or skill_instance.price,
            first_name=guardian.first_name,
            last_name=guardian.last_name,
            tx_ref=tx_ref
        )
        if response.get("status") != "success":
            return  Response({"status": "error", "message": response.get("message")}, status=400)
        valid_serializer.save(tx_ref=tx_ref, price=amount or skill_instance.price)
        return Response({"status": "success", "data": response.get("data")}, status=200)

class PaymentVerifyView(RetrieveAPIView):
    permission_classes = [IsPayOwner]

    def get(self, request, *args, **kwargs):
        tx_ref  = kwargs.get("tx_ref")
        if tx_ref is None:
            return Response({"status": "error", "message": "Transaction reference is required"}, status=400)

        serializer = PurchaseVerifySerializer(data=request.data, context={"request": request, "tx_ref": tx_ref})
        valid_serializer = _validate_serializer(serializer=serializer)

        purchase = get_pay_by_tx_ref_or_none(tx_ref=tx_ref, user=request.user)

        if purchase is None:
            return Response({"status": "error", "message": "Payment not found"}, status=404)

        payment = Payment()
        pay_verify = payment.verify_payment(purchase.tx_ref)
        if pay_verify["status"] == "success":
            payment_detail = pay_verify["data"]
            amount = payment_detail.get("amount")

            if not verify_payment_amount(purchase, amount):
                failed_purchase(purchase)
                return Response({"status": "error", "message": "Payment amount mismatch"}, status=400)
            
            if payment_detail["status"] == "success":
                completed_purchase(purchase)
            else:
                failed_purchase(purchase)
                return Response({"status": "error", "message": "Payment verification failed"}, status=400)
        else:
            return Response({"status": "error", "message": "Payment verification error"}, status=400)
        return Response({"status": "success", "data": {"payment_status": purchase.purchase_status}}, status=200)
