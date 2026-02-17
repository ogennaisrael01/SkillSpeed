from .services.tasks import send_email_on_quene, logger
from .services.helpers import _hash_otp_code, verify_otp
from .models import OneTimePassword, PasswordReset

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.contrib.auth.password_validation import (validate_password as _validate_password, 
                                                     MinimumLengthValidator)
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError

import email_validator
import logging


logger = logging.getLogger(__name__)

from typing import Optional

User = get_user_model()

def _send_email_to_user(context: dict):
    """
    Docstring for _send_email_to_user
    
    :param subject: Description
    :type subject: str
    :param template_name: Description
    :type template_name: str
    :param content: Description
    :type content: dict
    :param user: Description
    """
    if context is None:
        raise ValidationError("Missing Content Body")
    email = context.get("email")
    required_fields = ("email", "subject", "templete_name")
    if (context.get(field) for field in required_fields) is None:
        raise ValidationError("Please provides the required fields for email OTP.")
    if not User.objects.filter(email=email).exists():
        raise ValidationError("User dosent exits in our database")
    context.update({"to_email": email})
    try:
        send_email_on_quene.delay(context)
        logger.info(f"Email sent to quene for {email}")
        return {"success": True, "message": "Email sent to quene successfully"}
    except Exception:
        logger.exception("Exception while sending email.")
        raise

def _validate_email(email: str) -> dict:
    if email is None:
        raise ValidationError("Email field is emapty...")
    try:
        valid_email = email_validator.validate_email(email.strip(), check_deliverability=True)
    except email_validator.EmailNotValidError:
        raise 
    return {"success": True, "valid_email": valid_email.normalized}

def _check_email_already_exists(valid_email: str) -> bool:
    if valid_email is None:
        raise ValidationError("email field is emapty")
    if User.objects.filter(email=valid_email, is_active=True, is_verified=True):
        return True
    return False

def get_error_message():
    return _("No password Provided")

def _normalize_and_validate_password(password: str):
    if not password:
        raise ValidationError(get_error_message(), code="no_password")
    return _validate_password(password)


def _validate_serializer(serializer): 
    if serializer is None:
        raise ValidationError(_("Serializer is Empty"))
    serializer.is_valid(raise_exception=True)
    return serializer
    
def _get_user_by_email(email: str):
    try:
        user = User.objects.get(email=email)
        return user
    except User.DoesNotExist:
        return None

def _get_code(code: str, user:str = None):
    try:
        if user:
            one_time_password = OneTimePassword.objects.get(user=user, raw_code=code, is_active=True)
        else:
            one_time_password = OneTimePassword.objects.get(raw_code=code, is_active=True)
        if verify_otp(code, one_time_password.hash_code):
            return one_time_password
    except OneTimePassword.DoesNotExist:
        return None
    
def _verify_account(user, code_instance: OneTimePassword) -> dict:
        if not isinstance(user, User):
            raise ValidationError(_("'user is not a valid user instance"))
        try:
            with transaction.atomic():
                user.verify_account()
                code_instance.is_used = True
                code_instance.is_active = False
                code_instance.save(update_fields=["is_used", "is_active"])
            return {"success": True, "message": "Account verified successfully"}
        except IntegrityError:
            raise
        except Exception:
            raise ValidationError(_("Account verification due to common exception errors"))
        
def _get_reset_token_or_none(token):
    try:
        token = PasswordReset.objects.get(reset_token=token.strip(), is_active=True)
        return token
    except PasswordReset.DoesNotExist:
        return None
    
def save_user_password(user, password):
    account_status = getattr(user, "account_status")
    if account_status != "ACTIVE":
        return 
    user.set_password(password)
    user.save(update_fields=["password"])

def _get_reset_code_or_none(code):
    try:
        code_instance = PasswordReset.objects.get(raw_code=code, is_active=True)
        if verify_otp(code, code_instance.reset_code):
            return code_instance
    except PasswordReset.DoesNotExist:
        return None

def user_can_authenticate(user):
    if hasattr(user, "is_active") and hasattr(user, "is_verified"):
        return (getattr(user, "is_active", True) and 
                getattr(user, "is_verified", True))
    return False