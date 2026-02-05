from rest_framework.permissions import BasePermission


class IsPayOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request, "user"):
            user = request.user
            if not user.is_authenticated:
                return False
            if obj.purchased_by == user:
                return True
        return False