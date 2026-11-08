import uuid
from channels.db import database_sync_to_async

from django.conf import settings
from django.db import models

# Может, заменить PROTECT на CASCADE?
class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_rooms",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @staticmethod
    @database_sync_to_async
    def async_is_owner(user_id, room_id):
        # room = Room.objects.filter(pk=room_id)
        # return room.created_by.id == user_id
        return Room.objects.filter(pk=room_id, created_by_id=user_id).exists()
