from django.db import models

from ..skills.models import Skills
import uuid


class LessonContent(models.Model):
    class ContentStatus(models.TextChoices):
          IN_PROGRESS = "IN_PROGRESS"
          COMPLETED = "COMPLETED"

    class ContentType(models.TextChoices):
            VIDEO = "VIDEO"
            FILE = "FILE"
            TEXT = "TEXT"

    content_id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, max_length=20)

    skill = models.ForeignKey(Skills, on_delete=models.CASCADE, related_name="contents")

    title = models.CharField(max_length=500)
    description = models.TextField()

    content_type = models.CharField(choices=ContentType.choices, default=None)
    content_url  = models.URLField(null=True, blnak=True) # for file and video contents
    content_body = models.TextField(null=True, blank=True) # for text content 

    content_staus = models.CharField(choices=ContentStatus.choices, default=ContentStatus.IN_PROGRESS)
    content_order = models.PositiveIntegerField(default=1)
    current_level = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "lesson_contents"
        ordering = ["content_order"]

        constraints = [
            models.UniqueConstraint(fields=['skill', 'content_order'], name='unique_content_order_per_skill')
        ]
        indexes = [
            models.Index(fields=['skill', 'content_order']),
            models.Index(fields=['skill', 'content_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['content_status']),
            models.Index(fields=['current_level']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.skill.name}"
    
    def mark_as_completed(self):
        self.is_completed = True
        self.content_status = self.ContentStatus.COMPLETED
        self.completed_at = models.DateTimeField(auto_now=True)
        self.save()
    
    def deactivate(self):
        self.is_active = False
        self.save()
    


