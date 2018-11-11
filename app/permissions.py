from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    message = "Not an owner."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user == obj.user


class DisallowVoteChanges(permissions.BasePermission):
    message = "Can't update votes."

    def has_object_permission(self, request, view, obj):
        if request.data.get('downvotes') or request.data.get('upvotes'):
            return False
        return True