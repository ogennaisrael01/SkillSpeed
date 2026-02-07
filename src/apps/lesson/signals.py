from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone

from .models import Submission

import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Submission)
def set_time_submitted_after_submission(sender, instance, created, **kwargs):
    if not created:
        return 
    if not isinstance(instance, Submission):
        return  
    
    logger.debug("Signal fired for time submission")
    try:
        instance.submitted_at = timezone.now()
        instance.status = Submission.SubmissionStatus.SUBMITTED
        instance.save(update_fields=["submitted_at"])
        logger.debug("Successfully set time of submission")
    except Exception as e:
        logger.exception(f"error setting time of submission: {str(e)}")

