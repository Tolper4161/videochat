from rest_framework import serializers
from .models import Room, RoomParticipant, RoomJoinRequest

class RoomSerializer(serializers.ModelSerializer):
    creator_name = serializers.SerializerMethodField()
    invite_url_path = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ["id", "name", "creator", "creator_name", "invite_code", "invite_url_path", "status",
                  "is_private", "allow_guests", "scheduled_at", "participant_count", "created_at", "updated_at"]
        read_only_fields = ["id", "creator", "creator_name", "invite_code", "status", "invite_url_path",
                            "participant_count", "created_at", "updated_at"]

    def get_creator_name(self, obj):
        user = obj.creator
        return (getattr(user, "get_full_name", lambda: "")().strip()
                or getattr(user, "get_username", lambda: "")() or "Создатель")

    def get_invite_url_path(self, obj):
        return f"/api/rooms/invite/{obj.invite_code}/"

    def get_participant_count(self, obj):
        return obj.participants.filter(is_connected=True).count()


class RoomUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, max_length=100, allow_blank=False)

    class Meta:
        model = Room
        fields = ["name", "is_private", "allow_guests", "scheduled_at"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Название не может быть пустым.")
        room = self.instance
        if room and room.status == Room.Status.ACTIVE and value != room.name:
            raise serializers.ValidationError("Нельзя переименовать активную комнату.")
        if Room.objects.exclude(pk=getattr(room, "pk", None)).filter(name__iexact=value).exists():
            raise serializers.ValidationError("Комната с таким названием уже существует.")
        return value


class ParticipantSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    class Meta:
        model = RoomParticipant
        fields = ["id", "room", "user", "username", "display_name", "role", "is_connected", "is_muted", "joined_at", "left_at"]
        read_only_fields = fields

    def get_username(self, obj):
        return getattr(obj.user, "get_username", lambda: "")() if obj.user else None


class JoinRoomSerializer(serializers.Serializer):
    guest_name = serializers.CharField(max_length=100, required=False, allow_blank=False)


class JoinRequestSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    class Meta:
        model = RoomJoinRequest
        fields = ["id", "room", "user", "guest_name", "display_name", "status", "created_at", "decided_at"]
        read_only_fields = ["id", "room", "user", "status", "created_at", "decided_at", "display_name"]
