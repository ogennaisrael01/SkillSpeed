from django.db import models
from django.contrib.auth import get_user_model

from . import auth_models

import uuid

User = get_user_model()


class OneTimePassword(models.Model):
    otp_id = models.UUIDField(max_length=20,
                              default=uuid.uuid4,
                              primary_key=True,
                              unique=True,
                              db_index=True)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="one_time_codes")

    is_active = models.BooleanField(default=True, db_index=True)
    is_used = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    raw_code = models.CharField(unique=True, max_length=20)
    hash_code = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return f"OneTimePassword({self.user.email}, {self.is_active})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "hash_code"],
                                    name="unique_code_user")
        ]

        indexes = [
            models.Index(fields=["hash_code"], name="hash_cde_idx"),
            models.Index(fields=["is_active", "is_used"],
                         name='active_used_idx')
        ]

        verbose_name = "OneTimePassword"
        ordering = ["-created_at"]


class PasswordReset(models.Model):
    reset_id = models.UUIDField(primary_key=True,
                                max_length=20,
                                default=uuid.uuid4,
                                unique=True)
    reset_code = models.CharField(max_length=200,
                                  null=False,
                                  blank=False,
                                  db_index=True)
    reset_token = models.URLField(null=True, blank=True, db_index=True)
    raw_code = models.CharField(unique=True, max_length=20, db_index=True)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="reset_codes")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PasswordReset({self.user.email}, {self.is_active})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["reset_code", "user"],
                                    name="unique_reset_code_user"),
            models.UniqueConstraint(fields=["reset_token", "user"],
                                    name="unique_reset_user_user")
        ]

        indexes = [
            models.Index(fields=["is_active"], name="is_active_idx"),
            models.Index(fields=["is_active", "user", "reset_code"],
                         name="active_codes_idx")
        ]

        verbose_name = "ResetPassword"
