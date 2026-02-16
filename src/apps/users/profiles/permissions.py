from rest_framework .permissions import BasePermission

from django.contrib.auth import get_user_model

User = get_user_model()

class IsGuardian(BasePermission):
    """ A Base permission for checking users with guardian roles """
    def has_permission(self, request, view):
        if not hasattr(request, "user"): 
            return False
        user = request.user
        if not hasattr(user, "user_role"):
            return False
        if not user.is_authenticated:
            return False
        user_role = getattr(user, "user_role", None)
        if user_role is None:
            return False
        return (user_role == User.UserRoles.GUARDIAN)
    
    def has_object_permission(self, request, view, obj):
        if hasattr(request, "user"):
            user = request.user
            if not user.is_authenticated:
                return False
            if obj.user == user and user.user_role == User.UserRoles.GUARDIAN: 
                return True  
        return False
class IsAdminOrInstructor(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if user.user_role == User.UserRoles.INSTRUCTOR:
            return True
        return False

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request, "user"):
            user = request.user
            if not user.is_authenticated:
                return False
            return obj.user == user
        return False
    
class ChildProfileOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request, "user"):
            user = request.user
            if not user.is_authenticated:
                return False
            return getattr(obj, "guardian") == getattr(request, "user")
        return False

class ChildRole(BasePermission):
    def has_permission(self, request, view):
        if hasattr(request, "user"):
            user = request.user
            if not user.is_authenticated:
                return False
            if user.active_profile == User.ActiveProfile.CHILD:
                return True
        return False

class IsInterestOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if obj.child.guardian != user:
            return False
        return True
    
class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return getattr(user, "user_role") == User.UserRoles.INSTRUCTOR
    def has_object_permission(self, request, view, obj):
        return obj.user == getattr(request.user, "profile")