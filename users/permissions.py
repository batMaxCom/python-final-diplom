from rest_framework.permissions import BasePermission


class IsActivated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_verified)

class IsOwnerEmail(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.data['email'] == request.user.email)