from ..skills.models import Skills, Enrollment, ChildProfile
from .models import LessonContent, Progress, Projects

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.exceptions import ValidationError, NotFound

User = get_user_model()

def can_create_content(skill: Skills, user: User) -> bool:
    """ allow only skill owners/superusers to create skill content"""

    if user.is_superuser:
        return True
    return skill.user.user_id == user.id

def can_access_content(request, skill_pk):
        skill = get_object_or_404(Skills, pk=skill_pk, is_active=True)

        if request.user.pk == skill.user.pk:
             return True
        if request.user.is_superuser or request.user.is_staff:
            return True
        if Enrollment.objects.filter(skill=skill, child_profile=request.user.active_account, is_active=True):
             return True
        return False
        
def _get_contents_for_user(child_profile, skill: Skills):
    user_enrollment = Enrollment.objects.get(skill=skill, child_profile=child_profile, 
                                             is_active=True)
    contents = getattr(user_enrollment.skill, "contents ")
    return contents

def user_current_level(request, skill_pk):
    skill = get_object_or_404(Skills, pk=skill_pk, is_active=True)
    current_user_profile = getattr(request.user, "active_account")
    if not isinstance(current_user_profile, ChildProfile):
         raise ValidationError("The user does not have an active child profile. Please ensure the user has an active child profile to access this content.")
    contents = _get_contents_for_user(current_user_profile, skill)
    if contents is None:
         raise ValidationError("There are no contents to consume here, come back later")
    user_level = contents.current_level
    return user_level


def get_current_status(content: LessonContent):
    status = getattr(content, "content_status", None)
    if status is None:
         status = LessonContent.ContentStatus.IN_PROGRESS
    return status


def create_progress_record(child_profile, content):
    try:
        with transaction.atomic():
            Progress.objects.create(child_profile=child_profile, lesson_content=content)
    except Exception as e:
        raise ValidationError(f"An error occurred while creating progress record: {str(e)}")

def get_content_by_pk(content_pk) -> LessonContent:
    try:
        content = LessonContent.objects.get(pk=content_pk, is_active=True)
        return content
    except LessonContent.DoesNotExist:
        raise ValidationError("lesson content do not exists", code="content_do_no_exists")
    
def get_project_by_pk(project_pk):
    try:
        project = Projects.objects.get(pk=project_pk, is_active=True)
        return project
    except Projects.DoesNotExist:
        raise NotFound()
    except Exception:
        raise Exception()
    
def can_make_submission(request, project):
    try:
        active_child_profile = getattr(request.user, "active_account")
        skill = getattr(project.lesson_content, "skill")

        if Enrollment.objects.filter(skill=skill, child_profile=active_child_profile, is_active=True).exists():
            return True
        return False
    except Enrollment.DoesNotExist:
        raise NotFound()
    except Exception as e:
        raise ValidationError()
