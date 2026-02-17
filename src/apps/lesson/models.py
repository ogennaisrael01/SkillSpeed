from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from ..skills.models import Skills
from ..users.profiles.models import ChildProfile

import uuid


class LessonContent(models.Model):

    class ContentStatus(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS"
        COMPLETED = "COMPLETED"

    class ContentType(models.TextChoices):
        VIDEO = "VIDEO"
        FILE = "FILE"
        TEXT = "TEXT"

    content_id = models.UUIDField(primary_key=True,
                                  unique=True,
                                  default=uuid.uuid4,
                                  max_length=20)

    skill = models.ForeignKey(Skills,
                              on_delete=models.CASCADE,
                              related_name="contents")

    title = models.CharField(max_length=500)
    description = models.TextField()

    content_type = models.CharField(choices=ContentType.choices, default=None)
    content_url = models.URLField(null=True,
                                  blank=True)  # for file and video contents
    content_body = models.TextField(null=True, blank=True)  # for text content

    content_status = models.CharField(choices=ContentStatus.choices,
                                      default=ContentStatus.IN_PROGRESS)
    content_order = models.PositiveIntegerField(default=1)
    current_level = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "lesson_contents"
        ordering = ["content_order"]

        constraints = [
            models.UniqueConstraint(fields=['skill', 'content_order'],
                                    name='unique_content_order_per_skill')
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


class Progress(models.Model):
    progress_id = models.UUIDField(max_length=20,
                                   primary_key=True,
                                   unique=True,
                                   default=uuid.uuid4)

    child_profile = models.ForeignKey(ChildProfile,
                                      on_delete=models.CASCADE,
                                      related_name="progress")
    lesson_content = models.ForeignKey(LessonContent,
                                       on_delete=models.CASCADE,
                                       related_name="progress")

    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.child_profile} - {self.lesson_content}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["child_profile", "lesson_content"],
                                    name="unique_user_content")
        ]


class Projects(models.Model):

    class ProjectDifficulty(models.TextChoices):
        EASY = "EASY", "Easy"
        HARD = "HARD", "Hard"
        MEDIUM = "MEDIUM", 'Medium'

    project_id = models.UUIDField(primary_key=True,
                                  unique=True,
                                  default=uuid.uuid4,
                                  max_length=20)
    lesson_content = models.ForeignKey(LessonContent,
                                       on_delete=models.CASCADE,
                                       related_name="projects")

    title = models.CharField(max_length=500)
    instructions = models.TextField(null=False, blank=False)
    requirements = models.TextField(null=False, blank=False)
    description = models.TextField(null=False, blank=False)

    difficulty = models.CharField(choices=ProjectDifficulty.choices,
                                  default=None)

    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=['lesson_content']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['lesson_content', 'title'],
                name='unique_project_title_per_lesson_content')
        ]

    def __str__(self):
        return f"{self.title} - {self.lesson_content.title}"

    def deactivate(self):
        self.is_active = False
        self.save()


class Submission(models.Model):

    class SubmissionType(models.TextChoices):
        FILE = "FILE", "file"
        TEXT = "TEXT", "text"
        URL = 'URL', "url"

    class SubmissionStatus(models.TextChoices):
        SUBMITTED = "SUBMITTED", "submitted"
        APPROVED = "APPROVED", "approved"
        REJECT = "REJECT", "reject"

    submission_id = models.UUIDField(primary_key=True,
                                     unique=True,
                                     db_index=True,
                                     max_length=20,
                                     default=uuid.uuid4)

    project = models.ForeignKey(Projects,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                related_name="submissions")
    child_profile = models.ForeignKey(ChildProfile,
                                      on_delete=models.CASCADE,
                                      related_name="submissions")

    submission_type = models.CharField(choices=SubmissionType.choices,
                                       default=None)
    submission_text = models.TextField(null=True)
    submission_file = models.URLField(null=True)

    status = models.CharField(choices=SubmissionStatus.choices, default=None)
    feedback = models.TextField(null=True)
    work_rating = models.PositiveIntegerField(validators=[
        MinValueValidator(limit_value=1),
        MaxValueValidator(limit_value=5)
    ])
    instructors_points = models.PositiveIntegerField(validators=[
        MinValueValidator(limit_value=10),
        MaxValueValidator(limit_value=100)
    ])
    total_points_after_validatiokn = models.PositiveIntegerField()

    submitted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    approved_at = models.DateTimeField(blank=True, null=True, db_index=True)
    rejected_at = models.DateTimeField(blank=True, null=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.child_profile} - {self.project}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'child_profile'],
                name='unique_submission_per_project_per_user')
        ]
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"

        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['child_profile']),
            models.Index(fields=['status']),
        ]
