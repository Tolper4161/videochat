import secrets
import string
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

def make_invite_code(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

class Room(models.Model):
    class Status(models.TextChoices):
        INACTIVE = "inactive", "Неактивна"
        ACTIVE = "active", "Активна"
        ENDED = "ended", "Завершена"

    creator = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_room")
    name = models.CharField("Название", max_length=100)
    invite_code = models.CharField("Код приглашения", max_length=20, unique=True, default=make_invite_code, editable=False)
    status = models.CharField("Статус", max_length=10, choices=Status.choices, default=Status.INACTIVE)
    is_private = models.BooleanField("Требовать подтверждение входа", default=False)
    allow_guests = models.BooleanField("Разрешить гостям", default=True)
    scheduled_at = models.DateTimeField("Запланированное время", null=True, blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Комната"
        verbose_name_plural = "Комнаты"

    def __str__(self):
        return self.name

    @staticmethod
    def _base_name(user):
        full_name = ""
        get_full_name = getattr(user, "get_full_name", None)
        if callable(get_full_name):
            full_name = get_full_name().strip()
        username = getattr(user, "get_username", lambda: "")()
        return (full_name or username or "Комната")[:90]

    @classmethod
    def create_for_user(cls, user):
        # Return an existing room for this user, or create a room with a unique name.
        with transaction.atomic():
            existing = cls.objects.select_for_update().filter(creator=user).first()
            if existing:
                return existing, False
            base = cls._base_name(user)
            candidate = base
            suffix = 2
            while cls.objects.filter(name__iexact=candidate).exists():
                candidate = f"{base[:90 - len(str(suffix))]} {suffix}"
                suffix += 1
            room = cls.objects.create(creator=user, name=candidate)
            return room, True

    def rename(self, new_name):
        if self.status == self.Status.ACTIVE:
            raise ValidationError("Нельзя переименовать активную комнату.")
        new_name = (new_name or "").strip()
        if not new_name:
            raise ValidationError("Название комнаты не может быть пустым.")
        if len(new_name) > 100:
            raise ValidationError("Название комнаты не должно превышать 100 символов.")
        if Room.objects.exclude(pk=self.pk).filter(name__iexact=new_name).exists():
            raise ValidationError("Комната с таким названием уже существует.")
        self.name = new_name
        self.save(update_fields=["name", "updated_at"])

    def start(self):
        if self.status == self.Status.ACTIVE:
            raise ValidationError("Комната уже активна.")
        self.status = self.Status.ACTIVE
        self.save(update_fields=["status", "updated_at"])

    def end(self):
        self.status = self.Status.ENDED
        self.save(update_fields=["status", "updated_at"])


class RoomParticipant(models.Model):
    class Role(models.TextChoices):
        HOST = "host", "Создатель"
        GUEST = "guest", "Участник"

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="room_participations")
    display_name = models.CharField("Отображаемое имя", max_length=100)
    role = models.CharField("Роль", max_length=10, choices=Role.choices, default=Role.GUEST)
    is_connected = models.BooleanField("Подключён", default=True)
    is_muted = models.BooleanField("Микрофон выключен", default=False)
    joined_at = models.DateTimeField("Время входа", auto_now_add=True)
    left_at = models.DateTimeField("Время выхода", null=True, blank=True)

    class Meta:
        ordering = ["joined_at"]
        verbose_name = "Участник комнаты"
        verbose_name_plural = "Участники комнаты"
        constraints = [models.UniqueConstraint(fields=["room", "user"], condition=models.Q(user__isnull=False), name="unique_registered_user_per_room")]

    def __str__(self):
        return f"{self.display_name} — {self.room.name}"


class RoomJoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает решения"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="join_requests")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="room_join_requests")
    guest_name = models.CharField("Имя гостя", max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Заявка на вход"
        verbose_name_plural = "Заявки на вход"

    @property
    def display_name(self):
        if self.user:
            return (getattr(self.user, "get_full_name", lambda: "")().strip()
                    or getattr(self.user, "get_username", lambda: "")() or "Участник")
        return self.guest_name or "Гость"
