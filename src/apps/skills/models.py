from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

from ..users.profiles.models import ChildProfile

import uuid

User = get_user_model()


class SkillCategory(models.Model):

    class Category(models.TextChoices):
        TECH = "TECH", "Tech"
        VOCATIONAL = "VOCATIONAL", "Vocational"
        CRAFT = "CRAFT", "Craft"

    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL,
                             null=True,
                             related_name="category")
    category_id = models.UUIDField(primary_key=True,
                                   unique=True,
                                   max_length=20,
                                   default=uuid.uuid4)
    name = models.CharField(max_length=200,
                            choices=Category.choices,
                            default=None,
                            null=True,
                            unique=True)
    descriptions = models.TextField(max_length=1000, null=True, blank=True)

    icon = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("SkillCategory")
        indexes = [
            models.Index(fields=["name"], name="name_idx"),
            models.Index(fields=["category_id"], name="category_id_idx")
        ]
        ordering = ("name", )

    def __str__(self):
        return "SkillCategory({})".format(self.name)


class Skills(models.Model):

    class SkillDifficulty(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"

    skill_id = models.UUIDField(default=uuid.uuid4,
                                primary_key=True,
                                unique=True,
                                max_length=20)

    category = models.ForeignKey(SkillCategory,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 related_name="skills")
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="skills")
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    skill_difficulty = models.CharField(max_length=20,
                                        choices=SkillDifficulty.choices,
                                        default=SkillDifficulty.BEGINNER)

    min_age = models.PositiveIntegerField(validators=[
        MinValueValidator(5, message="Min age shouldn't be less than 5 "),
        MaxValueValidator(15, message="Max age shouldn't be grater than 15")
    ])
    max_age = models.PositiveIntegerField(validators=[
        MinValueValidator(5, message="Min age shouldn't be less than 5 "),
        MaxValueValidator(15, message="Max age shouldn't be grater than 15")
    ])
    price = models.DecimalField(max_digits=10,
                                decimal_places=2,
                                null=True,
                                blank=True)
    is_active = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "SKills({}, {})".format(self.name, self.category.name)

    class Meta:
        ordering = ("name", )
        verbose_name = _("skill")
        verbose_name_plural = _("skills")
        indexes = [
            models.Index(fields=['is_active'], name="is_active"),
            models.Index(fields=["is_deleted"], name="deleted_idx"),
            models.Index(fields=["name"], name="skill_name_idx"),
            models.Index(fields=["is_active", "is_deleted"],
                         name="deleted_active_idx")
        ]


class Enrollment(models.Model):
    enrol_id = models.UUIDField(primary_key=True,
                                unique=True,
                                max_length=20,
                                default=uuid.uuid4)

    child_profile = models.ForeignKey(ChildProfile,
                                      on_delete=models.CASCADE,
                                      related_name="enrollment")
    skill = models.ForeignKey(Skills,
                              on_delete=models.CASCADE,
                              related_name="enrollment")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", )
        indexes = [
            models.Index(fields=["is_active"], name="ac_idx"),
            models.Index(fields=["enrol_id"], name="enrol_idx")
        ]
        constraints = [
            models.UniqueConstraint(fields=["child_profile", "skill"],
                                    name="unique_profile_and_skill")
        ]

    def __str__(self):
        return "Enrollment({}, {})".format(self.child_profile.first_name,
                                           self.skill.name)
