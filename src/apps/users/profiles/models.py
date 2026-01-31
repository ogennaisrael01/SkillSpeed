from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

import uuid

User = get_user_model()

class Guardian(models.Model):
    guadian_id = models.UUIDField(primary_key=True, unique=True, max_length=20, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="guardian")

    display_name = models.CharField(max_length=200, null=True, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
                                     
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return _(f"Guardian profile {self.display_name}: {self.is_active}")
    
    class Meta:
        erbose_name = _("Guardian")
        verbose_name_plural = _("Guardians")
        indexes = [
            models.Index(fields=["is_active", "is_deleted"], name="active_deleted_idx")
        ]
        ordering = ("user",)

class ChildProfile(models.Model):
    class GenderChoices(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER",  "Other"

    child_id = models.UUIDField(primary_key=True, unique=True, max_length=20, default=uuid.uuid4)

    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name="child")

    gender = models.CharField(max_length=200, choices=GenderChoices.choices, default=None)
    date_of_birth = models.DateField(null=False, blank=False)

    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=200)

    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f" ChildProfile({self.child_id}, {self.guardian.pk})"
    
    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

        constraints = [
            models.UniqueConstraint(fields=["child_id", "guardian"], name="unique_child_guardian")
        ]
        indexes = [
            models.Index(fields=["child_id"], name="id_idx"),
            models.Index(fields=["is_active", "is_deleted"], name="active_idx")

        ]

        ordering = ("-created_at")

class ChildInterest(models.Model):
    interest_id = models.UUIDField(max_length=20, unique=True, primary_key=True, default=uuid.uuid4)

    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name="interest")

    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)

    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ChildInterest({self.child.pk})"

    
    class Meta:
        verbose_name = _("Interest")
        indexes = [
            models.Index(fields=["interest_id"], name="id_idx"),
            models.Index(fields=["is_active", "is_deleted"], name="act_idx")

        ]
        ordering = ("-created_at")



class Instructor(models.Model):
    pass