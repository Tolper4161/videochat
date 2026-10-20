from rest_framework.permissions import BasePermission

class IsRoomCreator(BasePermission):
    message = "Управлять этой комнатой может только её создатель."
    def has_object_permission(self, request, view, obj):
        room = getattr(obj, "room", obj)
        return bool(request.user and request.user.is_authenticated and room.creator_id == request.user.pk)

def is_room_creator(user, room):
    return bool(user and user.is_authenticated and room.creator_id == user.pk)
