from __future__ import absolute_import, unicode_literals

from rest_framework.exceptions import ValidationError

from celery import shared_task

from .email_service import _send_mail_base
from ..models import OneTimePassword

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
    :type content: dict
    """
    if content is None or any([value is None for value in content.values()]):
        raise ValidationError("Email content cannot be empty")
    send_email = _send_mail_base(context=content)
    if send_email:
        logger.info("Email message quened successfully")
    else:
        logger.error("Failed to quene email message")

@shared_task
def auto_expire_otp():
    with transaction.atomic():
        expired_otps = OneTimePassword.objects.filter(
            created_at__lt=timezone.now() - timezone.timedelta(minutes=OTP_life_span)
            ).update(is_active=~F("is_active"))

