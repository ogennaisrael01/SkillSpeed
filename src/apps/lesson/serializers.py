from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import LessonContent, Progress, Projects, Submission
from .helpers import can_create_content, Skills, can_make_submission
from ..skills.serializers import SkillReadSerializer
from .utils.services import validate_urls
from ..users.profiles.serializers import ChildReadSerializer

from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()

class LessonCreateSerializer(serializers.ModelSerializer):

    default_error_messages = {
        ""
    }
    class Meta:
        model = LessonContent
        fields = [
            "title", "description",
            "content_type", "content_url",
            "content_body", "content_order",
            "is_published"
        ]

    def validate(self, attrs):
        content_type_choices = LessonContent.ContentType.values

        content_type = attrs.get("content_type")
        if content_type not in content_type_choices:
            raise serializers.ValidationError(_(f"Invalid content type. Must be one of: {', '.join(content_type_choices)}"))
        
        if content_type in [LessonContent.ContentType.VIDEO, LessonContent.ContentType.FILE]:
            if not attrs.get("content_url"):
                raise serializers.ValidationError(_("content_url is required for VIDEO and FILE content types."))
            if not validate_urls(attrs["content_url"]):
                raise serializers.ValidationError(_("Invalid URL format for content_url."))
            
        if content_type == LessonContent.ContentType.TEXT:
            if not attrs.get("content_body"):
                raise serializers.ValidationError(_("content_body is required for TEXT content type."))
        return attrs

    def create(self, validated_data):
        if user is None:
            raise serializers.ValidationError(_("Auth credentials were not provided"), code="login_required")
        skill = self.context.get("skill")
        if not isinstance(skill, Skills):
            raise TypeError(_("Not a valid skill instance"))
        
        user = self.context["request"].user if self.context.get("request") else None
        if user is None:
            raise serializers.ValidationError(_("Auth credentials were not provided"), code="login_required")
        if not isinstance(user, User):
            raise TypeError(__("not a valid 'User', object"))
        
        
        if not can_create_content(skill, user):
            raise PermissionDenied()
        
        validated_data["title"] = validated_data["title"].title()
        with transaction.atomic():
            LessonContent.objects.create(skill=skill, **validated_data)
        return validated_data

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user
        if not isinstance(user, User):
            raise TypeError(__("not a valid 'User', object"))
        
        if instance.skill.user.pk != user.pk:
            raise PermissionDenied()
        instance.save()
        return instance
        
class LessonReadSerializer(serializers.ModelSerializer):
    skill = SkillReadSerializer(read_only=True, many=True)
    class Meta:
        model = LessonContent
        fields = [
            "skill", "title",
            "description", "content_type",
            "content_url", "content_body",
            "content_status", "content_order",
            "current_level", 'is_active',
            "is_completed", "is_published",
            "created_at", "completed_at"
        ]

class ProjectSerializer(serializers.ModelSerializer):
    lesson_content = LessonReadSerializer(read_only=True, many=True)
    duration = serializers.SerializerMethodField()
    class Meta:
        model = Projects
        fields = [
            "lesson_content",
            "description", "title",
            "instructions", "description",
            "difficulty", "is_required",
            "start_date", "end_date",
            "created_at", "duration"
        ]
        read_only_fields = [
            "lesson_content", "created_at",
            "duration"
        ]
    default_error_messages = {
        "invalid_dates": _("end_date must be greater than start_date."),
        "detailed_instruction": _("Please give a detailed instruction of this project.")
    }
    
    def get_duration(self, obj):
        start_date = getattr(obj, "start_date")
        end_date = getattr(obj, "end_date")
        durations = start_date - end_date
        return f"{durations}(s)"

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        if start_date >= end_date:
            self.fail("invalid_dates")
        return attrs
    
    def validate_instructions(self, value):
        if len(value) < 10:
            self.fail("detailed_instruction")
        return value
    
    def create(self, validated_data):
        request = self.context.get("request")
        content = self.context.get("content")
        if not can_create_content(skill=content.skill, user=request.user):
            raise PermissionDenied()
        with transaction.atomic():
            Projects.objects.create(lessont_content=content, **validated_data)

        return validated_data

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user")
        skill = getattr(instance.lesson_content, "skill")

        if not can_create_content(skill, user):
            raise PermissionDenied()
        with transaction.atomic():
            instance.save()
        return instance       


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission 
        fields = [
            "submission_type", "submission_text",
            "submission_file", 

        ]
    default_error_messages = {
        "no_submission_type": _("Please provide accurate submission type."),
        "no_file_content": _("Please provide the accurate file content"),
        "no_text_content": _("Please provide accurate text content for this submission")
    }
    def validate(self, attrs: dict):
        submission_type = attrs.get("submission_type")
        if submission_type is None:
            self.fail("no_submission_type")
        
        if submission_type in (Submission.SubmissionType.FILE, Submission.SubmissionType.URL) \
            and attrs["submission_file"] is None or not validate_urls(attrs["submission_file"]):
            self.fail("no_file_content")
        
        elif submission_type == Submission.SubmissionType.TEXT and \
            attrs["submission_text"] is None:
            self.fail("no_text_content")
        
        return attrs
    
    def create(self, validated_data):
        request = self.context.get("request")
        project = self.context.get("project")
        if not can_make_submission(request, project):
            raise PermissionDenied()
        child_profile = getattr(request.user, "active_account")
        try:
            with transaction.atomic():
                Submission.objects.create(project=project, child_profile=child_profile, **validated_data)

        except Exception as e:
            raise serializers.ValidationError(_(f"Error creating submissions: {str(e)}"), code="invalid_request")
        return validated_data        

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if not can_make_submission(request, instance.project):
            raise PermissionDenied()
        try:
            with transaction.atomic():
                instance.save()
        except Exception as e:
            raise serializers.ValidationError(_(f"Error updating request: {str(e)}"), code="invalid_request")

        return instance
            
class FeebBackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = [
            "feedback", "work_rating",
            "instructor_points"
        ]
    default_error_messages = {
        "value_too_small": _("Feedback must be at least 10 characters long."),
        "value_must_between_1_and_5": _("Work rating must be between 1 and 5.")
    }
        
    def validate_instructor_points(self, value):
        "in between 10 and 100"
        if not 10 <= value <= 100:
            raise serializers.ValidationError(_("Instructor point must be between 10 and 100."))
        return value

    def validate_feedback(self, value):
        if len(value) < 10:
            self.fail("value_too_small")
        return value
    
    def validate_work_rating(self, value):
        if not 1 <= value <= 5:
            self.fail("value_must_between_1_and_5")
        return value
    
    def update(self, instance, validated_data):
        request = self.context.get("request")
        skill = getattr(instance.project.lesson_content, "skill")
        if not can_create_content(skill, request.user):
            raise PermissionDenied()

        project_end_date = instance.project.end_date
        current_date = timezone.now().date()
        if current_date > project_end_date: # project is expired
            instance.total_points_after_validatiokn = validated_data["instructor_points"] - 5 # minus 5 points for late submission
        try:
            with transaction.atomic():
                instance.reviewed_at = timezone.now()
                instance.save()
        except Exception as e:
            raise serializers.ValidationError(_(f"error seeding feedback: {str(e)}"), code="invalid_request")
        return instance

class AcceptRejectProjectSerializer(serializers.ModelSerializer):
    choices = [Submission.SubmissionStatus.APPROVED, Submission.SubmissionStatus.REJECT]

    status = serializers.ChoiceField(choices=choices, write_only=True, required=True)
    class Meta:
        model = Submission
        fields = [
            "status"
        ]
    default_error_messages = {
        "invalid_value": _("Invalid status value. Must be either 'APPROVED' or 'REJECT'."),
        "can_update": _("Invalid request. You can only approve or reject already submitted projects")
    }
    def validate_status(self, value):
        if value not in self.choices:
            self.fail("invalid_value")
        return value

    def update(self, instance, validated_data):
        request = self.context.get("request")
        skill = getattr(instance.project.lesson_content, "skill")
        if not can_create_content(skill, request.user):
            raise PermissionDenied()
        
        if instance.status != Submission.SubmissionStatus.SUBMITTED:
            self.fail("can_update")

        status = validated_data.get("status")
        if status.upper() == Submission.SubmissionStatus.APPROVED:
            instance.status = status.upper()
            instance.approved_at = timezone.now()
        elif status.upper() == Submission.SubmissionStatus.REJECT:
            instance.status = status.upper()
            instance.rejected_at = timezone.now()
        
        try:
            with transaction.atomic():
                instance.save()
        except Exception as e:
            raise serializers.ValidationError(f"Error updating status: {str(e)}", code="request_rejected")
        return instance
    
class SubmissionReadSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True, many=True)
    child_profile = ChildReadSerializer(read_only=True, many=True)
    class Meta:
        model = serializers
        fields = [
            "project", "child_profile",
            "submission_type", "submission_text",
            "submission_file", 'status',
            "feedback", "work_rating",
            "instructor_points", "total_points_after_validation",
            "submitted_at", "approved_at", 
            "rejected_at", "reviewed_at",
            "created_at"
        ] 