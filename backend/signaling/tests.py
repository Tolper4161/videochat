from datetime import datetime
from unittest.mock import patch, AsyncMock

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase
from signaling.models import RoomParticipantService, GroupException, Participant
from signaling.consumers import SignalingConsumer
from rooms.models import Room
from users.models import User
from signaling.routing import websocket_urlpatterns
import uuid


class RoomParticipantServiceTest(SimpleTestCase):

    def setUp(self):
        super().setUp()

        self.service = RoomParticipantService()
        self.room_id = uuid.uuid4()
        self.user_id = 5
        self.channel_name = "channel_name"
        self.username = "username"

    async def test_add_client_to_non_exists_room(self):
        with self.assertRaises(GroupException) as context:
            await self.service.add_consumer(self.room_id, self.user_id, self.channel_name, self.username)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4409, "Комнаты для подключения не существует"))

    ## ТЕСТЫ ДЛЯ ПРОВЕРКИ ПОДКЛЮЧЕНИЯ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ К ЗВОНКУ
    async def test_add_client_where_client_owner(self):
        self.service.consumers[self.room_id] = {}

        ## Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True

            with self.assertRaises(GroupException) as context:
                await self.service.add_consumer(self.room_id, self.user_id, self.channel_name, self.username)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4400, "Попытка повторного подключения к комнате"))

    async def test_add_client_already_exists_in_this_room(self):
        participant = Participant(uuid.uuid4(), self.user_id, self.room_id, self.channel_name,
                                  self.username, datetime.now(), False, False, False)

        self.service.consumers[self.room_id] = {participant.participant_id: participant}

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False

            with self.assertRaises(GroupException) as context:
                await self.service.add_consumer(self.room_id, self.user_id, self.channel_name, self.username)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4423, "Попытка повторного подключения к комнате"))

    async def test_add_client_already_exists_in_other_room(self):
        some_room_id = uuid.uuid4()

        participant = Participant(uuid.uuid4(), self.user_id, some_room_id, self.channel_name,
                                  self.username, datetime.now(), False, False, False)

        self.service.consumers[self.room_id] = {}
        self.service.consumers[some_room_id] = {participant.participant_id: participant}

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False

            with self.assertRaises(GroupException) as context:
                await self.service.add_consumer(self.room_id, self.user_id, self.channel_name, self.username)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4423, "Пользователь уже состоит в другой комнате"))

    async def test_add_client(self):
        self.service.consumers[self.room_id] = {}

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False

            participant_id = await self.service.add_consumer(self.room_id, self.user_id, self.channel_name,
                                                             self.username)

        self.assertIsInstance(participant_id, uuid.UUID)
        self.assertEqual(len(self.service.consumers), 1)
        self.assertEqual(len(self.service.consumers[self.room_id]), 1)
        self.assertIn(participant_id, self.service.consumers[self.room_id])

        participant = self.service.consumers[self.room_id][participant_id]
        self.assertEqual(participant.participant_id, participant_id)
        self.assertEqual(participant.room_id, self.room_id)
        self.assertEqual(participant.user_id, self.user_id)
        self.assertEqual(participant.channel_name, self.channel_name)
        self.assertEqual(participant.username, self.username)
        self.assertFalse(participant.is_owner)
        self.assertFalse(participant.micro_muted)
        self.assertFalse(participant.camera_enabled)

    ## ТЕСТЫ ДЛЯ ПРОВЕРКИ СОЗДАНИЯ КОМНАТЫ ЗВОНКОМ
    async def test_add_owner_not_his_room(self):
        ## Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False

            with self.assertRaises(GroupException) as context:
                await self.service.add_owner(self.room_id, self.user_id, self.channel_name, self.username)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4003, "Отказано в доступе"))

    async def test_add_owner_room_already_exists(self):
        self.service.consumers[self.room_id] = {}

        ## Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True

            with self.assertRaises(GroupException) as context:
                await self.service.add_owner(self.room_id, self.user_id, self.channel_name, self.username)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4409, "Комната уже существует"))

    async def test_add_owner_already_exists_in_other_room(self):
        some_room_id = uuid.uuid4()

        participant = Participant(uuid.uuid4(), self.user_id, some_room_id, self.channel_name,
                                  self.username, datetime.now(), False, False, False)

        self.service.consumers[some_room_id] = {participant.participant_id: participant}

        ## Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True

            with self.assertRaises(GroupException) as context:
                await self.service.add_owner(self.room_id, self.user_id, self.channel_name, self.username)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4423, "Пользователь уже имеет активное подключение"))

    async def test_add_owner(self):
        ## Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True

            participant_id = await self.service.add_owner(self.room_id, self.user_id, self.channel_name, self.username)

        self.assertIsInstance(participant_id, uuid.UUID)
        self.assertEqual(len(self.service.consumers), 1)
        self.assertEqual(len(self.service.consumers[self.room_id]), 1)
        self.assertIn(participant_id, self.service.consumers[self.room_id])

        participant = self.service.consumers[self.room_id][participant_id]
        self.assertEqual(participant.participant_id, participant_id)
        self.assertEqual(participant.room_id, self.room_id)
        self.assertEqual(participant.user_id, self.user_id)
        self.assertEqual(participant.channel_name, self.channel_name)
        self.assertEqual(participant.username, self.username)
        self.assertTrue(participant.is_owner)
        self.assertFalse(participant.micro_muted)
        self.assertFalse(participant.camera_enabled)

    ## ТЕСТ НА ПРОВЕРКУ УДАЛЕНИЯ ПОДКЛЮЧЕНИЯ ИЗ КОМНАТЫ
    async def test_delete_non_exists_participant(self):
        participant = Participant(uuid.uuid4(), self.user_id, self.room_id, self.channel_name,
                                  self.username, datetime.now(), False, False, False)

        second_participant = Participant(uuid.uuid4(), self.user_id, self.room_id, self.channel_name,
                                         self.username, datetime.now(), False, False, False)

        self.service.consumers[self.room_id] = {participant.participant_id: participant}
        self.service.consumers[self.room_id][second_participant.participant_id] = second_participant

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False

            with self.assertRaises(GroupException) as context:
                await self.service.delete_participant(self.room_id, uuid.uuid4())

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4404, "Не удалось найти активное подключение для разрыва соединения"))

        self.assertIn(participant.participant_id, self.service.consumers[self.room_id])
        self.assertIn(second_participant.participant_id, self.service.consumers[self.room_id])

    async def test_delete_participant_non_exists_room(self):
        participant = Participant(uuid.uuid4(), self.user_id, self.room_id, self.channel_name,
                                  self.username, datetime.now(), False, False, False)
        second_participant = Participant(uuid.uuid4(), self.user_id, self.room_id, self.channel_name,
                                         self.username, datetime.now(), False, False, False)

        self.service.consumers[self.room_id] = {participant.participant_id: participant}
        self.service.consumers[self.room_id][second_participant.participant_id] = second_participant

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False

            with self.assertRaises(GroupException) as context:
                await self.service.delete_participant(uuid.uuid4(), participant.participant_id)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4404, "Не удалось найти активное подключение для разрыва соединения"))

        self.assertIn(participant.participant_id, self.service.consumers[self.room_id])
        self.assertIn(second_participant.participant_id, self.service.consumers[self.room_id])

    async def test_delete_participant(self):
        participant = Participant(uuid.uuid4(), self.user_id, self.room_id, self.channel_name,
                                  self.username, datetime.now(), False, False, False)

        second_participant = Participant(uuid.uuid4(), self.user_id, self.room_id, self.channel_name,
                                         self.username, datetime.now(), False, False, False)

        self.service.consumers[self.room_id] = {participant.participant_id: participant}
        self.service.consumers[self.room_id][second_participant.participant_id] = second_participant

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False

            await self.service.delete_participant(self.room_id, participant.participant_id)

        self.assertNotIn(participant.participant_id, self.service.consumers[self.room_id])
        self.assertIn(second_participant.participant_id, self.service.consumers[self.room_id])

    ## ТЕСТ НА ПРОВЕРКУ УДАЛЕНИЯ КОМНАТЫ
    async def test_delete_non_exists_room(self):
        self.service.consumers[self.room_id] = {}

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True

            flag = await self.service.delete_room(uuid.uuid4())

        self.assertFalse(flag)
        self.assertIn(self.room_id, self.service.consumers)

    async def test_delete_room(self):
        self.service.consumers[self.room_id] = {}

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True

            flag = await self.service.delete_room(self.room_id)

        self.assertTrue(flag)
        self.assertNotIn(self.room_id, self.service.consumers)

    ## ТЕСТЫ НА ПРОВЕРКУ get_participants_by_room_id
    async def test_get_participants_non_exists_room(self):
        self.service.consumers[uuid.uuid4()] = {}

        with self.assertRaises(GroupException) as context:
            await self.service.get_participants_by_room_id(self.room_id)

        self.assertEqual((context.exception.code, str(context.exception)),
                         (4409, "Комнаты для подключения не существует"))

    async def test_get_participants(self):
        self.service.consumers[self.room_id] = {}

        array = await self.service.get_participants_by_room_id(self.room_id)

        self.assertIsInstance(array, list)


class SignalingTestStartCall(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.application = URLRouter(websocket_urlpatterns)

    def setUp(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

    async def test_start_call_success(self):
        communicator = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator.scope["user"] = self.user1

        connected, protocol = await communicator.connect()

        ## Проверяем, что подключиться удалось
        self.assertTrue(connected)

        ## Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await communicator.send_json_to({'type': 'start_call'})

            response = await communicator.receive_json_from()

        self.assertEqual(response, {'type': 'call_started'})

        ## Проверяем, что в словаре consumers появилась запись с room_id
        self.assertIn(self.room_id, SignalingConsumer.room_service.consumers)

        await communicator.disconnect()

    async def test_start_call_not_owner(self):
        communicator = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator.scope["user"] = self.user2

        connected, protocol = await communicator.connect()

        ## Проверяем, что подключиться удалось
        self.assertTrue(connected)

        ## Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await communicator.send_json_to({'type': 'start_call'})

            response = await communicator.receive_json_from()

        self.assertEqual(response, {'type': 'error', 'payload': {'code': 4003, 'message': 'Отказано в доступе',
                                                                 'request_type': 'start_call'}})

        self.assertNotIn(self.room_id, SignalingConsumer.room_service.consumers)

        await communicator.disconnect()

    async def test_start_call_call_already_exists(self):
        communicator = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator.scope["user"] = self.user1

        connected, protocol = await communicator.connect()

        # Проверяем, что подключиться удалось
        self.assertTrue(connected)

        # Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await communicator.send_json_to({'type': 'start_call'})
            await communicator.receive_json_from()

            # Отправляем повторный запрос на начало звонка
            await communicator.send_json_to({'type': 'start_call'})
            response = await communicator.receive_json_from()

        self.assertEqual(response, {'type': 'error', 'payload': {'code': 4409, 'message': 'Комната уже существует',
                                                                 'request_type': 'start_call'}})

        self.assertIn(self.room_id, SignalingConsumer.room_service.consumers)

        await communicator.disconnect()

    async def test_start_call_anonymous_user(self):
        communicator = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator.scope["user"] = AnonymousUser()

        connected, protocol = await communicator.connect()

        self.assertFalse(connected)

    async def test_start_call_user_in_smth_call(self):
        communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator1.scope["user"] = self.user1

        connected1, protocol1 = await communicator1.connect()

        communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator2.scope["user"] = self.user2

        connected2, protocol2 = await communicator2.connect()

        self.assertTrue(connected1)
        self.assertTrue(connected2)

        ## Задаём mock-заглушку для того, чтобы сымитировать обращение к БД
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await communicator1.send_json_to({'type': 'start_call'})
            await communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await communicator2.send_json_to({'type': 'join'})
            await communicator2.receive_json_from()

        communicator3 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room2.id}')
        communicator3.scope["user"] = self.user2

        await communicator3.connect()

        # Пытаемся создать комнату будучи в другом звонке
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await communicator3.send_json_to({'type': 'start_call'})
            response = await communicator3.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4423, 'message': 'Пользователь уже имеет активное подключение',
                                                'request_type': 'start_call'}})

        # Проверяем, что в словаре consumers не появилась запись с room2
        self.assertNotIn(self.room2.id, SignalingConsumer.room_service.consumers)


class SignalingTestJoin(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.application = URLRouter(websocket_urlpatterns)

    def setUp(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

    async def test_join_success(self):
        communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator1.scope["user"] = self.user1

        connected1, protocol1 = await communicator1.connect()

        communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator2.scope["user"] = self.user2

        connected2, protocol2 = await communicator2.connect()

        self.assertTrue(connected1)
        self.assertTrue(connected2)

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await communicator1.send_json_to({'type': 'start_call'})
            await communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await communicator2.send_json_to({'type': 'join'})
            response2 = await communicator2.receive_json_from()
            response1 = await communicator1.receive_json_from()

        self.assertIn('type', response1)
        self.assertEqual(response1['type'], 'participant_joined')

        self.assertIn('payload', response1)
        self.assertIn('participant_id', response1['payload'])
        self.assertIn('username', response1['payload'])
        self.assertIn('micro_muted', response1['payload'])
        self.assertIn('camera_enabled', response1['payload'])

        self.assertEqual(response1['payload']['micro_muted'], False)
        self.assertEqual(response1['payload']['camera_enabled'], False)
        self.assertEqual(response1['payload']['username'], self.user2.username)

        self.assertIn('type', response2)
        self.assertEqual(response2['type'], 'joined')

        self.assertIn('payload', response2)
        self.assertIn('participant_id', response2['payload'])
        self.assertIn('participants', response2['payload'])
        self.assertEqual(len(response2['payload']['participants']), 1)

        self.assertEqual(response2['payload']['participants'][0]['camera_enabled'], False)
        self.assertEqual(response2['payload']['participants'][0]['micro_muted'], False)
        self.assertEqual(response2['payload']['participants'][0]['username'], self.user1.username)

        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_join_client_is_owner(self):
        communicator = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator.scope["user"] = self.user1

        connected, protocol = await communicator.connect()

        self.assertTrue(connected)

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await communicator.send_json_to({'type': 'start_call'})
            await communicator.receive_json_from()

            await communicator.send_json_to({'type': 'join'})
            response = await communicator.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Попытка повторного подключения к комнате',
                                                'request_type': 'join'}})

        await communicator.disconnect()

    async def test_join_room_not_exists(self):
        communicator = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator.scope["user"] = self.user1

        connected, protocol = await communicator.connect()

        self.assertTrue(connected)

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False

            await communicator.send_json_to({'type': 'join'})
            response = await communicator.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4409, 'message': 'Комнаты для подключения не существует',
                                                'request_type': 'join'}})

        await communicator.disconnect()

    async def test_join_double_try_join(self):
        communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator1.scope["user"] = self.user1

        connected1, protocol1 = await communicator1.connect()

        communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        communicator2.scope["user"] = self.user2

        connected2, protocol2 = await communicator2.connect()

        self.assertTrue(connected1)
        self.assertTrue(connected2)

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await communicator1.send_json_to({'type': 'start_call'})
            await communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await communicator2.send_json_to({'type': 'join'})
            await communicator2.receive_json_from()
            await communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await communicator2.send_json_to({'type': 'join'})
            response = await communicator2.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4423, 'message': 'Попытка повторного подключения к комнате',
                                                'request_type': 'join'}})

        await communicator1.disconnect()
        await communicator2.disconnect()


class SignalingLeave(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.application = URLRouter(websocket_urlpatterns)

    def setUp(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

        self.communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator1.scope["user"] = self.user1

        self.communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator2.scope["user"] = self.user2

    async def create(self):
        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await self.communicator2.send_json_to({'type': 'join'})
            await self.communicator2.receive_json_from()
            await self.communicator1.receive_json_from()

    async def test_leave_success(self):
        await self.create()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await self.communicator2.send_json_to({'type': 'leave'})

            close_event = await self.communicator2.receive_output()

        response = None
        if close_event == {'type': 'websocket.close'}:
            await self.communicator2.disconnect()
            response = await self.communicator1.receive_json_from()

        self.assertIn('type', response)
        self.assertIn('payload', response)
        self.assertIn('participant_id', response['payload'])

        self.assertIn(self.room_id, SignalingConsumer.room_service.consumers)
        self.assertEqual(len(SignalingConsumer.room_service.consumers[self.room_id]), 1)

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_leave_client_is_owner(self):
        await self.create()
        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'leave'})
            response = await self.communicator1.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4403, 'message': 'Отказано в доступе',
                                                'request_type': 'leave'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_leave_client_not_in_call(self):
        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await self.communicator2.send_json_to({'type': 'leave'})
            response = await self.communicator2.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Пользователь не состоит ни в одной комнате',
                                                'request_type': 'leave'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()


class SignalingEndCall(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.application = URLRouter(websocket_urlpatterns)

    def setUp(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

        self.communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator1.scope["user"] = self.user1

        self.communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator2.scope["user"] = self.user2

    async def create(self):
        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await self.communicator2.send_json_to({'type': 'join'})
            response2 = await self.communicator2.receive_json_from()
            await self.communicator1.receive_json_from()
        self.participant_id2 = response2['payload']['participant_id']
        self.participant_id1 = response2['payload']['participants'][0]['participant_id']

    async def test_end_call_success(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'end_call'})
        close_event = await self.communicator1.receive_output()

        close_participant = None
        if close_event == {'type': 'websocket.close'}:
            await self.communicator1.disconnect()
            close_participant = await self.communicator2.receive_json_from()

        self.assertEqual(close_participant, {'type': 'call_ended', 'payload': {'reason': 'owner_ended'}})
        self.assertNotIn(self.room_id, SignalingConsumer.room_service.consumers)

        close_event = await self.communicator2.receive_output()

        if close_event == {'code': 4000, 'type': 'websocket.close'}:
            self.assertEqual(close_event, {'code': 4000, 'type': 'websocket.close'})
            await self.communicator2.disconnect()

    async def test_end_call_client_try(self):
        await self.create()

        await self.communicator2.send_json_to({'type': 'end_call'})
        response = await self.communicator2.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4403, 'message': 'Нет прав для завершения звонка',
                                                'request_type': 'end_call'}})
        self.assertIn(self.room_id, SignalingConsumer.room_service.consumers)

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_end_call_not_active_call(self):
        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        await self.communicator2.send_json_to({'type': 'end_call'})
        response = await self.communicator2.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Пользователь не состоит ни в одной комнате',
                                                'request_type': 'end_call'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()


class SignalingOffer(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.application = URLRouter(websocket_urlpatterns)

    def setUp(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

        self.communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator1.scope["user"] = self.user1

        self.communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator2.scope["user"] = self.user2

    async def create(self):
        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await self.communicator2.send_json_to({'type': 'join'})
            response2 = await self.communicator2.receive_json_from()
            await self.communicator1.receive_json_from()

        self.participant_id2 = response2['payload']['participant_id']
        self.participant_id1 = response2['payload']['participants'][0]['participant_id']

    async def test_offer_success(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'offer', 'payload': {'to': self.participant_id2, 'sdp': 'some_data'}})

        response = await self.communicator2.receive_json_from()
        self.assertEqual(response, {'type': 'offer', 'payload': {'from': self.participant_id1, 'sdp': 'some_data'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_offer_no_adresat(self):
        await self.create()

        await self.communicator1.send_json_to(
            {'type': 'offer', 'payload': {'to': str(uuid.uuid4()), 'sdp': 'some_data'}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Пользователи не состоят в одной комнате',
                                                'request_type': 'offer'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_offer_adresat_in_different_call(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

        self.communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator1.scope["user"] = self.user1

        self.communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room2.id}')
        self.communicator2.scope["user"] = self.user2

        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator2.send_json_to({'type': 'start_call'})
            await self.communicator2.receive_json_from()

        self.participant_id2 = None
        for key in SignalingConsumer.room_service.consumers[self.room2.id]:
            self.participant_id2 = key

        await self.communicator1.send_json_to(
            {'type': 'offer', 'payload': {'to': str(self.participant_id2), 'sdp': 'some_data'}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Пользователи не состоят в одной комнате',
                                                'request_type': 'offer'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_offer_no_sdp(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'offer', 'payload': {'to': self.participant_id2}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                   'payload': {'code': 1011, 'message': 'Произошла внутренняя ошибка сервера',
                                               'request_type': 'offer'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_offer_no_to(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'offer', 'payload': {'sdp': 's'}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                   'payload': {'code': 1011, 'message': 'Произошла внутренняя ошибка сервера',
                                               'request_type': 'offer'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()


class SignalingAnswer(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.application = URLRouter(websocket_urlpatterns)

    def setUp(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

        self.communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator1.scope["user"] = self.user1

        self.communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator2.scope["user"] = self.user2

    async def create(self):
        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await self.communicator2.send_json_to({'type': 'join'})
            response2 = await self.communicator2.receive_json_from()
            await self.communicator1.receive_json_from()

        self.participant_id2 = response2['payload']['participant_id']
        self.participant_id1 = response2['payload']['participants'][0]['participant_id']

    async def test_answer_success(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'answer', 'payload': {'to': self.participant_id2, 'sdp': 'some_data'}})

        response = await self.communicator2.receive_json_from()
        self.assertEqual(response, {'type': 'answer', 'payload': {'from': self.participant_id1, 'sdp': 'some_data'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_answer_no_adresat(self):
        await self.create()

        await self.communicator1.send_json_to(
            {'type': 'answer', 'payload': {'to': str(uuid.uuid4()), 'sdp': 'some_data'}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Пользователи не состоят в одной комнате',
                                                'request_type': 'answer'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_answer_adresat_in_different_call(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

        self.communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator1.scope["user"] = self.user1

        self.communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room2.id}')
        self.communicator2.scope["user"] = self.user2

        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator2.send_json_to({'type': 'start_call'})
            await self.communicator2.receive_json_from()

        self.participant_id2 = None
        for key in SignalingConsumer.room_service.consumers[self.room2.id]:
            self.participant_id2 = key

        await self.communicator1.send_json_to(
            {'type': 'answer', 'payload': {'to': str(self.participant_id2), 'sdp': 'some_data'}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Пользователи не состоят в одной комнате',
                                                'request_type': 'answer'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_answer_no_sdp(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'answer', 'payload': {'to': self.participant_id2}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                   'payload': {'code': 1011, 'message': 'Произошла внутренняя ошибка сервера',
                                               'request_type': 'answer'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_answer_no_to(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'answer', 'payload': {'sdp': 's'}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                   'payload': {'code': 1011, 'message': 'Произошла внутренняя ошибка сервера',
                                               'request_type': 'answer'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()


class SignalingCandidate(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.application = URLRouter(websocket_urlpatterns)

    def setUp(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

        self.communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator1.scope["user"] = self.user1

        self.communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator2.scope["user"] = self.user2

    async def create(self):
        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = False
            await self.communicator2.send_json_to({'type': 'join'})
            response2 = await self.communicator2.receive_json_from()
            await self.communicator1.receive_json_from()

        self.participant_id2 = response2['payload']['participant_id']
        self.participant_id1 = response2['payload']['participants'][0]['participant_id']

    async def test_candidate_success(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'ice_candidate', 'payload': {'to': self.participant_id2, 'candidate': {}}})

        response = await self.communicator2.receive_json_from()
        self.assertEqual(response, {'type': 'ice_candidate', 'payload': {'to': self.participant_id2, 'candidate': {}}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_candidate_no_adresat(self):
        await self.create()

        await self.communicator1.send_json_to(
            {'type': 'ice_candidate', 'payload': {'to': str(uuid.uuid4()), 'candidate': {}}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Пользователи не состоят в одной комнате',
                                                'request_type': 'ice_candidate'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_candidate_adresat_in_different_call(self):
        self.user1 = User(id=1, username='user1', email='yandex@yandex.ru', password='1234567890')
        self.room1 = Room(uuid.uuid4(), "room_user1", 1)

        self.user2 = User(id=2, username='user2', email='gamil@gamil.com', password='1234567890')
        self.room2 = Room(uuid.uuid4(), "room_user2", 2)

        self.room_id = self.room1.id

        self.communicator1 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room_id}')
        self.communicator1.scope["user"] = self.user1

        self.communicator2 = WebsocketCommunicator(self.application, f'/ws/signaling/{self.room2.id}')
        self.communicator2.scope["user"] = self.user2

        self.connected1, self.protocol1 = await self.communicator1.connect()
        self.connected2, self.protocol2 = await self.communicator2.connect()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator1.send_json_to({'type': 'start_call'})
            await self.communicator1.receive_json_from()

        with patch.object(Room, "async_is_owner", new_callable=AsyncMock) as mock:
            mock.return_value = True
            await self.communicator2.send_json_to({'type': 'start_call'})
            await self.communicator2.receive_json_from()

        self.participant_id2 = None
        for key in SignalingConsumer.room_service.consumers[self.room2.id]:
            self.participant_id2 = key

        await self.communicator1.send_json_to(
            {'type': 'ice_candidate', 'payload': {'to': str(self.participant_id2), 'candidate': {}}})

        response = await self.communicator1.receive_json_from()
        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 4400, 'message': 'Пользователи не состоят в одной комнате',
                                                'request_type': 'ice_candidate'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_candidate_no_candidate_field(self):
        await self.create()

        await self.communicator1.send_json_to(
            {'type': 'ice_candidate', 'payload': {'to': self.participant_id2}})

        response = await self.communicator1.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                   'payload': {'code': 1011, 'message': 'Произошла внутренняя ошибка сервера',
                                               'request_type': 'ice_candidate'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_candidate_no_to(self):
        await self.create()

        await self.communicator1.send_json_to({'type': 'ice_candidate', 'payload': {'candidate': {}}})

        response = await self.communicator1.receive_json_from()

        self.assertEqual(response, {'type': 'error',
                                    'payload': {'code': 1011, 'message': 'Произошла внутренняя ошибка сервера',
                                                'request_type': 'ice_candidate'}})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()

    async def test_candidate_is_const(self):
        await self.create()

        await self.communicator1.send_json_to(
            {'type': 'ice_candidate', 'payload': {'to': self.participant_id2, 'candidate': {'a': 'b'}}})

        response1 = await self.communicator2.receive_json_from()

        await self.communicator2.send_json_to(
            {'type': 'ice_candidate', 'payload': {'to': self.participant_id1, 'candidate': response1['payload']['candidate']}})

        response2 = await self.communicator1.receive_json_from()

        self.assertEqual(response1['payload']['candidate'], {'a': 'b'})
        self.assertEqual(response2['payload']['candidate'], {'a': 'b'})

        await self.communicator1.disconnect()
        await self.communicator2.disconnect()
