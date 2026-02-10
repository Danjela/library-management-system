from rest_framework.permissions import BasePermission


def user_in_group(user, group_name: str) -> bool:
    return (
        user.is_authenticated
        and user.groups.filter(name=group_name).exists()
    )

class IsMember(BasePermission):
    def has_permission(self, request, view):
        return user_in_group(request.user, "MEMBER")


class IsLibrarian(BasePermission):
    def has_permission(self, request, view):
        return user_in_group(request.user, "LIBRARIAN")
