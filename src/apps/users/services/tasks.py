from __future__ import absolute_import, unicode_literals

from rest_framework.exceptions import ValidationError

from celery import shared_task

from .email_service import _send_mail_base
from ..models import OneTimePassword, PasswordReset

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from django.utils.translation import gettext_lazy as _

import logging 

logger = logging.getLogger(__name__)
OTP_life_span = getattr(settings, "OTP_LIFE")

@shared_task
def send_email_on_quene(content: dict):
    """
    Docstring for send_email_on_quene
    
    :param content: Description
    :type content: 
    """
    try:
        _send_mail_base(context=content)
    except Exception:
        raise
    else:
        logger.error("Failed to quene email message")

@shared_task
def auto_expire_otp():
    with transaction.atomic():
        expired_otps = OneTimePassword.objects.filter(
            created_at__lt=timezone.now() - timezone.timedelta(minutes=OTP_life_span)
            ).update(is_active=~F("is_active"))

@shared_task
def auto_deactivate_reset_code():
    with transaction.atomic():
        PasswordReset.objects.filter(
            created_at__lt=timezone.now() - timezone.timedelta(minutes=OTP_life_span)
            ).update(is_active=~F("is_active"))
