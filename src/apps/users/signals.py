from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

from .services.helpers import (create_otp_for_user, 
                               _genrate_url_for_account_verification)
from .helpers import _send_email_to_user, logger
from .services.templates_service import genrate_context_for_otp

User = get_user_model()

@receiver(post_save, sender=User)
def post_save_otp_after_account_registration(sender, instance, created, **kwargs):
    """ Automatically create and send OTP and verification URL to user after account registration """
    if not isinstance(instance, User):
        return 
    if not created: 
        return
    logger.debug(f"Signal fired for user: {instance.email}")
    try:
        code = create_otp_for_user(instance)
        url = _genrate_url_for_account_verification(code)
        context = genrate_context_for_otp(code, url, instance.email)
        _send_email_to_user(context)
        logger.debug(f"OTP created and email sent for user: {instance.email}")
    except Exception as e:
        logger.error(f"Error in post_save signal for {instance.email}: {e}")


