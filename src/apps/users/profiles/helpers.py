from .models import Guardian, Instructor, ChildProfile

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from rest_framework.exceptions import ValidationError

from uuid import UUID
from typing import Tuple

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

def child_in_guardian_account(user: User, child_pk: UUID) -> Tuple[bool, ChildProfile]:
    children = getattr(user, "children", None)
    if children is None:
        raise ValidationError(_("No active child guardian profile for this user"))
    child_profile = ChildProfile.objects.get(pk=child_pk, is_active=True)
    if child_profile in children.all():
        return True, child_profile
    return False, child_profile