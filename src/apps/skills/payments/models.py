from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from ..models import Skills, ChildProfile

import uuid

User = get_user_model()


class Purchase(models.Model):

    class PurchaseStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        FAILED = "FAILED", "Failed"
        COMPLETED = "COMPLETED", "Completed"

    purchase_id = models.UUIDField(primary_key=True,
                                   unique=True,
                                   max_length=20,
                                   default=uuid.uuid4)

    skill = models.ForeignKey(Skills,
                              on_delete=models.SET_NULL,
                              null=True,
                              related_name="purchases")
    purchased_by = models.ForeignKey(User,
                                     on_delete=models.CASCADE,
                                     related_name="purchases")
    purchased_for = models.ForeignKey(ChildProfile,
                                      on_delete=models.CASCADE,
                                      related_name="purchases")
    purchase_status = models.CharField(choices=PurchaseStatus.choices,
                                       default=PurchaseStatus.PENDING,
                                       max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tx_ref = models.CharField(max_length=200, unique=True, null=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Purchase {self.purchase_id} - {self.skill} by {self.purchased_by}"

    class Meta:
        verbose_name = _("Purchase")
        verbose_name_plural = _("Purchases")
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['purchase_id']),
            models.Index(fields=['tx_ref']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['tx_ref'],
                                    name='unique_tx_ref_per_purchase'),
            models.UniqueConstraint(fields=['skill', "purchased_for"],
                                    name='unique_purchase_id'),
        ]
