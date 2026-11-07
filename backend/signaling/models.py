import uuid
import asyncio

from datetime import datetime
from rooms.models import Room


class GroupException(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class Participant:
    def __init__(self, participant_id=None, user_id=None, room_id=None, channel_name=None, username=None,
                 joined_at=None, is_owner=None, micro_muted=None, camera_enabled=None):
        self.participant_id = participant_id
        self.user_id = user_id
        self.room_id = room_id
        self.channel_name = channel_name
        self.username = username,
        self.joined_at = joined_at
        self.is_owner = is_owner
        self.micro_muted = micro_muted
        self.camera_enabled = camera_enabled


# На всех consumers будет один единственный RoomParticipantService
# RoomParticipantService хранит словарь, где по ключу (room_id) лежит другой словарь
# Этот словарь по participant_id хранит соответсвующий объект Participant

# !!! Можно при проверке на то, что пользователь состоит хотя бы в какой-нибудь комнате, исключать из цикла
# текущую комнату при условии, что она была проверена на пребывание пользователя в ней !!!

class RoomParticipantService:
    def __init__(self):
        self.consumers = {}
        self.locker = asyncio.Lock()

    async def delete_room(self, room_id):
        async with self.locker:

            if room_id in self.consumers:
                del self.consumers[room_id]
                return True
            return False

    async def delete_participant(self, room_id, participant_id):
        async with self.locker:

            if room_id in self.consumers:
                if participant_id in self.consumers[room_id]:
                    del self.consumers[room_id][participant_id]
                    return

            raise GroupException(4404, "Не удалось найти активное подключение для разрыва соединения")

    # Добавляем consumer (не owner!) в группу и возвращаем participant_id
    async def add_consumer(self, room_id, user_id, channel_name, username):
        async with self.locker:

            # Если комнаты ранее не было в consumers
            if room_id not in self.consumers: raise GroupException(4409, "Комнаты для подключения не существует")

            # Если к своей комнате пытается подключиться owner как обычный пользователь
            if await Room.async_is_owner(user_id, room_id): raise GroupException(4400, "Попытка повторного "
                                                                                       + "подключения к комнате")

            # Если пользователь уже состоит в данной комнате
            for key in self.consumers[room_id]:
                if self.consumers[room_id][key].user_id == user_id: raise GroupException(4423, "Попытка повторного "
                                                                                               + "подключения к комнате")

            # Если пользователь уже состоит в какой-нибудь комнате
            if self.user_has_active_call(user_id): raise GroupException(4423, "Пользователь уже состоит "
                                                                              + "в другой комнате")

            participant_id = uuid.uuid4()
            new_participant = Participant(participant_id, user_id, room_id, channel_name, username, datetime.now(), False, False, False)
            self.consumers[room_id][participant_id] = new_participant

        return participant_id

    # Создаем комнату и автоматически добавляем туда владельца как участника
    async def add_owner(self, room_id, user_id, channel_name, username):
        async with self.locker:

            # Если комната уже существует
            if room_id in self.consumers: raise GroupException(4409, "Комната уже существует")

            # Если комнату пытается создать не её владелец
            if not(await Room.async_is_owner(user_id, room_id)): raise GroupException(4003, "Отказано в доступе")

            # Если пользователь уже состоит в какой-нибудь комнате
            if self.user_has_active_call(user_id): raise GroupException(4423, "Пользователь уже "
                                                                              + "имеет активное подключение")

            participant_id = uuid.uuid4()
            new_participant = Participant(participant_id, user_id, room_id, channel_name, username, datetime.now(), True, False, False)
            self.consumers[room_id] = {}
            self.consumers[room_id][participant_id] = new_participant

        return participant_id

    # Метод только для пользования в рамках объекта класса!
    def user_has_active_call(self, user_id):
        # Можно оптимизировать и не проверять звонок с room_id, если до этого эта комната уже была проверена
        for room_id in self.consumers:
            for key in self.consumers[room_id]:
                if self.consumers[room_id][key].user_id == user_id: return True
        return False

    async def user_in_room(self, room_id, participant_id):
        async with self.locker: return participant_id in self.consumers[room_id]

    async def is_owner(self, room_id, participant_id):
        async with self.locker: return self.consumers[room_id][participant_id].is_owner

    async def is_consumers_in_same_room(self, room_id, participant_id_1, participant_id_2):
        async with self.locker:
            return (participant_id_1 in self.consumers[room_id]) and (participant_id_2 in self.consumers[room_id])

    async def get_user_channel_name(self, room_id, participant_id):
        async with self.locker:
            return self.consumers[room_id][participant_id].channel_name

    async def get_participants_by_room_id(self, room_id):
        async with self.locker:
            participants_array = []
            for key in self.consumers[room_id]:
                current_participant = self.consumers[room_id][key]

                participants_array.append(
                    {
                        "username": current_participant.username,
                        "participant_id": str(current_participant.participant_id),
                        "micro_muted": bool(current_participant.micro_muted),
                        "camera_enabled": bool(current_participant.camera_enabled)
                    }
                )
            return participants_array

    async def set_micro_status(self, room_id, participant_id, status):
        async with self.locker:
            self.consumers[room_id][participant_id].micro_muted = bool(status)

    async def set_camera_status(self, room_id, participant_id, status):
        async with self.locker:
            self.consumers[room_id][participant_id].camera_enabled = bool(status)
