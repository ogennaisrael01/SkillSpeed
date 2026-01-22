from __future__ import absolute_import, unicode_literals

from rest_framework.exceptions import ValidationError

from celery import shared_task

from .email_service import _send_mail_base

import logging 

logger = logging.getLogger(__name__)

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
        return
    else:
        logger.error("Failed to quene email message")
        return



