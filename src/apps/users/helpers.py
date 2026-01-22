from .services.tasks import send_email_on_quene, logger

from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError

User = get_user_model()

def _send_email_to_user(subject: str, template_name:str, content:dict, user):
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
    if not isinstance(user, User):
        logger.error("User is not a valid custom user instance")
        raise ValidationError("'user' is not a valid 'CustomUser' instance")
    if not subject:
        raise ValidationError("Email requires a subject")
    if not template_name:
        raise ValidationError("Please provide a template name to send well structured notifications")
    if content is None:
        raise ValidationError("Missing Content Body")
    if not User.objects.filter(email=user.email).exists():
        raise ValidationError("User dosent exits in our database")
    email = user.email
    content.update({"to_email": email, "subject": subject, "template_name": template_name})
    try:
        send_email_on_quene.delay(content)
    except Exception:
        logger.exception("Exception while sending email.")
        raise
    

    
    
        
