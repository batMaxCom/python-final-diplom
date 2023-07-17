from rest_framework.permissions import BasePermission


class IsActivated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_verified)


class IsShop(BasePermission):
    message = 'Вы должы быть Поставщиком!'
    def has_permission(self, request, view):
        return bool(request.user.type == 'shop')
