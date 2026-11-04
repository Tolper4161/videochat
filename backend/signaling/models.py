import uuid
import asyncio

from datetime import datetime
from rooms.models import Room


class GroupException(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class Participant:
    def __init__(self, participant_id=None, user_id=None, room_id=None, joined_at=None, is_owner=None):
        self.participant_id = participant_id
        self.user_id = user_id
        self.room_id = room_id
        self.joined_at = joined_at
        self.is_owner = is_owner


# На всех consumers будет один единственный RoomPermissionsService
# RoomPermissionsService хранит словарь, где по ключу (room_id) лежит другой словарь
# Этот словарь по participant_id хранит соответсвующий объект Participant

# !!! Можно при проверке на то, что пользователь состоит хотя бы в какой-нибудь комнате, исключать из цикла
# текущую комнату при условии, что она была проверена на пребывание пользователя в ней !!!

class RoomPermissionsService:
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
    async def add_consumer(self, room_id, user_id):
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
            if await self.user_has_active_call(user_id): raise GroupException(4423, "Пользователь уже состоит "
                                                                              + "в другой комнате")

            participant_id = uuid.uuid4()
            new_participant = Participant(participant_id, user_id, room_id, datetime.now(), False)
            self.consumers[room_id][participant_id] = new_participant

        return participant_id

    # Создаем комнату и автоматически добавляем туда владельца как участника
    async def add_owner(self, room_id, user_id):
        async with self.locker:

            # Если комната уже существует
            if room_id in self.consumers: raise GroupException(4409, "Комната уже существует")

            # Если комнату пытается создать не её владелец
            if not(await Room.async_is_owner(user_id, room_id)): raise GroupException(4003, "Отказано в доступе")

            # Если пользователь уже состоит в какой-нибудь комнате
            if await self.user_has_active_call(user_id): raise GroupException(4423, "Пользователь уже "
                                                                              + "имеет активное подключение")

            participant_id = uuid.uuid4()
            new_participant = Participant(participant_id, user_id, room_id, datetime.now(), True)
            self.consumers[room_id] = {}
            self.consumers[room_id][participant_id] = new_participant

        return participant_id

    async def user_has_active_call(self, user_id):
        # Можно оптимизировать и не проверять звонок с room_id, если до этого эта комната уже была проверена
        async with self.locker:

            for room_id in self.consumers:
                for key in self.consumers[room_id]:
                    if self.consumers[room_id][key].user_id == user_id: return True

        return False

    async def user_in_room(self, room_id, participant_id):
        async with self.locker: return participant_id in self.consumers[room_id]

    async def is_owner(self, room_id, participant_id):
        async with self.locker: return self.consumers[room_id][participant_id].is_owner
