from rest_framework.permissions import BasePermission

class CanUpdateSubmission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user")
        if not user.is_authenticated:
            return False
        if user.active_account == obj.child_profile:
            return True
        return False