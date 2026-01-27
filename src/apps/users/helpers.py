from .services.tasks import send_email_on_quene, logger

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction 
from django.contrib.auth.password_validation import (validate_password as _validate_password, 
                                                     MinimumLengthValidator)
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError

import email_validator

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
    subject = context.get("subject")
    template_name = context.get("template_name")
    if not email:
        raise ValidationError("email cannot be empty")
    if not subject:
        raise ValidationError("Email requires a subject")
    if not template_name:
        raise ValidationError("Please provide a template name to send well structured notifications")
    
    if not User.objects.filter(email=email).exists():
        raise ValidationError("User dosent exits in our database")
    email = email
    context.update({"to_email": email, "subject": subject, "template_name": template_name})
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
    with transaction.atomic():
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
    

    
    
        
