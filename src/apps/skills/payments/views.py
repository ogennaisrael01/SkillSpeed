from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from .serializers import PurchaseSerializer
from ...users.helpers import _validate_serializer
from ...users.profiles.permissions import ChildRole, IsGuardian
from .payments import Payment
from ..models import Skills, ChildProfile

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
        response = payment._initialize_payment(
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