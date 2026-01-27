from django.db import models
from django.contrib.auth import get_user_model

from . import auth_models

import uuid

User = get_user_model()

class OneTimePassword(models.Model):
    otp_id = models.UUIDField(max_length=20, default=uuid.uuid4, primary_key=True, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="one_time_codes")

    is_active = models.BooleanField(default=True, db_index=True)
    is_used = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    hash_code = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return f"OneTimePassword({self.user.email}, {self.is_active})"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "hash_code"], name="unique_code_user")
        ]

        indexes = [
            models.Index(fields=["hash_code"], name="hash_cde_idx"),
            models.Index(fields=["is_active", "is_used"], name='active_used_idx')
        ]
        
        verbose_name = "OneTimePassword"
        ordering = ["-created_at"]
