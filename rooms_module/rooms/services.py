from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from .models import Room, RoomParticipant, RoomJoinRequest

def ensure_creator(user, room):
    if not user or not user.is_authenticated or room.creator_id != user.pk:
        raise PermissionDenied("Действие доступно только создателю комнаты.")

def display_name_for_user(user):
    return (getattr(user, "get_full_name", lambda: "")().strip()
            or getattr(user, "get_username", lambda: "")() or "Участник")

def join_room(room, *, user=None, guest_name=""):
    if room.status == Room.Status.ENDED:
        raise ValidationError("Звонок в этой комнате завершён.")
    if user and user.is_authenticated:
        existing = room.participants.filter(user=user).first()
        name = display_name_for_user(user)
    else:
        if not room.allow_guests:
            raise PermissionDenied("В этой комнате запрещён вход гостям.")
        name = (guest_name or "").strip()
        if not name:
            raise ValidationError("Для гостевого входа укажите имя.")
        existing = None

    if room.is_private:
        request_obj = RoomJoinRequest.objects.create(
            room=room, user=user if user and user.is_authenticated else None,
            guest_name="" if user and user.is_authenticated else name,
        )
        return None, request_obj

    if existing:
        existing.is_connected = True
        existing.left_at = None
        existing.display_name = name
        existing.save(update_fields=["is_connected", "left_at", "display_name"])
        return existing, None

    participant = RoomParticipant.objects.create(
        room=room, user=user if user and user.is_authenticated else None,
        display_name=name, role=RoomParticipant.Role.GUEST, is_connected=True,
    )
    return participant, None

def leave_room(participant):
    participant.is_connected = False
    participant.left_at = timezone.now()
    participant.save(update_fields=["is_connected", "left_at"])

def decide_join_request(request_obj, *, approved):
    if request_obj.status != RoomJoinRequest.Status.PENDING:
        raise ValidationError("Заявка уже рассмотрена.")
    room = request_obj.room
    if approved and room.status == Room.Status.ENDED:
        raise ValidationError("Нельзя подключиться к завершённой комнате.")
    request_obj.status = RoomJoinRequest.Status.APPROVED if approved else RoomJoinRequest.Status.REJECTED
    request_obj.decided_at = timezone.now()
    request_obj.save(update_fields=["status", "decided_at"])
    participant = None
    if approved:
        participant = RoomParticipant.objects.create(
            room=room, user=request_obj.user, display_name=request_obj.display_name,
            role=RoomParticipant.Role.GUEST,
        )
    return participant
