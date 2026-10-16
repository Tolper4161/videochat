from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Room, RoomJoinRequest
from .services import join_room, leave_room

User = get_user_model()

class RoomModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="test-pass-123")

    def test_create_for_user_returns_same_room(self):
        room1, created1 = Room.create_for_user(self.user)
        room2, created2 = Room.create_for_user(self.user)
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(room1.pk, room2.pk)

    def test_name_collision_gets_suffix(self):
        user2 = User.objects.create_user(username="alice2", password="test-pass-123")
        Room.objects.create(creator=self.user, name="alice")
        room, created = Room.create_for_user(user2)
        self.assertTrue(created)
        self.assertEqual(room.name, "alice2")

    def test_cannot_rename_active_room(self):
        room, _ = Room.create_for_user(self.user)
        room.start()
        with self.assertRaises(ValidationError):
            room.rename("New name")

    def test_guest_can_join_and_leave(self):
        room, _ = Room.create_for_user(self.user)
        participant, request_obj = join_room(room, guest_name="Guest")
        self.assertIsNone(request_obj)
        self.assertTrue(participant.is_connected)
        leave_room(participant)
        participant.refresh_from_db()
        self.assertFalse(participant.is_connected)

    def test_private_room_creates_request(self):
        room, _ = Room.create_for_user(self.user)
        room.is_private = True
        room.save()
        participant, request_obj = join_room(room, guest_name="Guest")
        self.assertIsNone(participant)
        self.assertEqual(request_obj.status, RoomJoinRequest.Status.PENDING)

class RoomApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="test-pass-123")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_my_room(self):
        response = self.client.post("/api/rooms/me/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "alice")

    def test_creator_can_start_room(self):
        room, _ = Room.create_for_user(self.user)
        response = self.client.post(f"/api/rooms/{room.pk}/start/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        room.refresh_from_db()
        self.assertEqual(room.status, Room.Status.ACTIVE)
