from .models import Guardian, Instructor

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from rest_framework.exceptions import ValidationError

User = get_user_model()

def create_guadian_profile(user: User):
    if not isinstance(user, User):
        raise ValidationError(_("'user' is not a valid 'User' instance"))
    with transaction.atomic():
        Guardian.objects.create(user=user, display_name=user.get_full_name_or_none())

def create_instructor_profile(user: User):
    if not isinstance(user, User):
        raise ValidationError(_("'user' is not a valid 'User' instance"))
    with transaction.atomic():
        Instructor.objects.create(user=user, display_name=user.get_full_name_or_none())
