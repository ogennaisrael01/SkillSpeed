from django.db import models
from django.utils.translation import gettext_lazy as _

import uuid

class SkillCategory(models.Model):
    class Category(models.TextChoices):
        TECH = "TECH", "Tech"
        VOCATIONAL = "VOCATIONAL", "Vocational"
        CRAFT = "CRAFT", "Craft"
    
    category_id = models.UUIDField(primary_key=True, unique=True, max_length=20, default=uuid.uuid4)
    name = models.CharField(max_length=200, choices=Category.choices, default=None, null=True)
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
        ordering = ("name",)

    def __str__(self):
        return "SkillCategory({})".format(self.name)