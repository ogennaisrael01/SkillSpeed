from django.db import models
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

import uuid


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str = None, user_role=None, **extra_fields):
        """"""
        if not all([email]):
            raise ValueError("Email is required")
        valid_email = self.normalize_email(email)
        user = self.model(email=valid_email, user_role=None, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password = None, **extra_fields):
        user = self.create_user(email=email, password=password, **extra_fields)
        setattr(user, "is_superuser", True)
        setattr(user, "is_staff", True)
        user.save(using=self._db)
        return user
    

class CustomUser(AbstractBaseUser, PermissionsMixin):
    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        DEACTIVATED = "DEACTIVATED", "Deactivated"

    class UserRoles(models.TextChoices):
        INSTRUCTOR =  "INSTRUCTOR", "Instructor"
        GUARDIAN = "GUARDIAN", "Guardian"

    user_id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4)
    email = models.EmailField(unique=True, max_length=200)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    user_role = models.CharField(max_length=200, choices=UserRoles.choices, default=None, null=True, blank=True)

    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # account status
    account_status = models.CharField(max_length=200, 
                                      choices=AccountStatus.choices,
                                        default=AccountStatus.ACTIVE) # active, suspended, deactivated
    #timastamp
    verified_at = models.DateTimeField(blank=True, null=True)
    suspended_at = models.DateTimeField(blank=True, null=True)
    deactivated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def suspend_account(self):
        if isinstance(self, CustomUser):
            if hasattr(self, "account_status"):
                self.account_status = self.AccountStatus.SUSPENDED
                self.suspended_at = timezone.now()
                self.save()
        return False

    def deactivate_account(self):
        if isinstance(self, CustomUser):
            if hasattr(self, "account_status"):
                self.account_status = self.AccountStatus.DEACTIVATED
                self.deactivated_at = timezone.now()
                self.save()
        return False
    
    def verify_account(self):
        if isinstance(self, CustomUser):
            if hasattr(self, "is_verified"):
                setattr(self, "is_verified", True)
                setattr(self, "is_active", True)
                setattr(self, "verified_at", timezone.now())
                self.save()
        return False
    
    def get_full_name_or_none(self):
        if all([self.first_name, self.last_name]):
            return self.first_name + " " + self.last_name
        return None
    
    @property
    def is_admin(self):
        return (
            self.is_superuser,
            self.is_staff
        )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["email"], name="unique_email")
        ]
        indexes = [
            models.Index(fields=["is_active", "account_status"], name="active_status_idx"),
            models.Index(fields=["email"], name="email_idx"),
            models.Index(fields=["created_at"], name="time_idx"),
        ]
