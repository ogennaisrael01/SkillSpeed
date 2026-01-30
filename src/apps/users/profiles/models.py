from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

import uuid

User = get_user_model()

class ChildProfile(models.Model):
    pass 

class Guardian(models.Model):
    guardian_id = models.UUIDField(primary_key=True, unique=True, max_length=20, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="guardian")

    children = models.ForeignKey(ChildProfile, on_delete=models.SET_NULL, null=True, blank=True)
    display_name = models.CharField(max_length=200, null=True, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
                                     
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return _(f"Guardian profile {self.display_name}: {self.is_active}")
    
    class Meta:
        verbose_name = _("Guardian")
        verbose_name_plural = _("Guardians")

        constraints = [
            models.UniqueConstraint(fields=["user", "children"], name="unique_guardian_and_child")
        ]
        indexes = [
            models.Index(fields=["is_active", "is_deleted"], name="active_deleted_idx")
        ]
        ordering = ("user",)
