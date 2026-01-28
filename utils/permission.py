from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.utils import timezone
from .exceptions import PaymentRequired


class IsAdmin(BasePermission):
    """
    Allows access only to users where is_admin=True.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class RolePermission(BasePermission):
    """
    Allow access only to users with specific roles.
    Define allowed_roles in the view.
    """
    def has_permission(self, request, view):
        allowed_roles = getattr(view, "allowed_roles", [])
        return (
            request.user.is_authenticated
            and request.user.role in allowed_roles
        )


class IsOwnerOrParentHierarchy(BasePermission):
    """
    Grants access if:
    - user is the owner
    - OR the authenticated user is a parent, or parent of parent (recursive)
    """
    def has_object_permission(self, request, view, obj):
        # obj = target user or account
        target_user = getattr(obj, "user", obj)  # for AccountSerializer

        if request.user == target_user:
            return True  # User accessing own data

        # Traverse upward recursively
        parent = target_user.parent
        while parent:
            if parent == request.user:
                return True
            parent = parent.parent

        return False
    
    
class HasActiveSubscription(BasePermission):

    def has_permission(self, request, view):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return False  # DRF will handle 401/403

        sub = getattr(user, "subscription", None)

        if not sub:
            raise PaymentRequired("No active subscription. Please recharge.")

        # auto-expire
        if sub.status == "active" and sub.expires_at and timezone.now() >= sub.expires_at:
            sub.status = "expired"
            sub.save(update_fields=["status"])
            raise PaymentRequired("Subscription expired. Please recharge.")

        if not sub.is_active():
            raise PaymentRequired("Subscription expired. Please recharge.")

        return True
