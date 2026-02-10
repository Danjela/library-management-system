from rest_framework.permissions import BasePermission

class IsReservationOwner(BasePermission):
    def has_object_permission(self, request, view, reservation):
        return reservation.member.user_id == request.user.id
