from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'

class IsHR(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'hr'

class IsCandidate(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'candidate'