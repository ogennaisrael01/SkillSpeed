from .models import Purchase

from django.contrib.auth import get_user_model
from django.db import transaction


def get_pay_by_tx_ref_or_none(tx_ref, user):
    User = get_user_model()
    if not isinstance(user, User):
        return None
    try:
        payment = Purchase.objects.get(tx_ref=tx_ref, purchased_by=user)
    except Purchase.DoesNotExist:
        return None
    except Exception:
        return None
    return payment

def completed_purchase(payment: Purchase):
    with transaction.atomic():
        payment.purchase_status = Purchase.PurchaseStatus.COMPLETED
        payment.save(update_fields=["purchase_status"])
        
    
def failed_purchase(payment: Purchase):
    with transaction.atomic():
        payment.purchase_status = Purchase.PurchaseStatus.FAILED
        payment.save(update_fields=["purchase_status"])
        return True
    
def is_payment_completed(payment: Purchase):
    return payment.purchase_status == Purchase.PurchaseStatus.COMPLETED

def is_payment_failed(payment: Purchase):
    return payment.purchase_status == Purchase.PurchaseStatus.FAILED

def is_payment_pending(payment: Purchase):
    return payment.purchase_status == Purchase.PurchaseStatus.PENDING

def can_access_skill(payment: Purchase):
    return is_payment_completed(payment)

def verify_payment_amount(payment: Purchase, amount: float):
    return float(payment.price) == float(amount)


