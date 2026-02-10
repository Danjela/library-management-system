from rest_framework.permissions import BasePermission


class IsBorrowerOrLibrarian(BasePermission):

    def has_object_permission(self, request, view, loan):
        user = request.user

        if user.groups.filter(name="LIBRARIAN").exists():
            return True
        
        return loan.member.user == request.user
