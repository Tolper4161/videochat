from channels.generic.websocket import AsyncJsonWebsocketConsumer

from signaling.models import RoomParticipantService, GroupException
from signaling.ws_types import WebSocketType
import json
import uuid

# consumer_type - для отправки типа запроса пользователям группы
# type при отправке сообщения пользователям группы
# (не на frontend!) содержит имя метода, который должен выполниться внутри consumer


class SignalingConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_uuid = None
        self.room_group_name = None
        self.user = None
        self.participant_id = None

    room_service = None

    @classmethod
    def initialize_room_service(cls):
        if cls.room_service is None: cls.room_service = RoomParticipantService()

    @classmethod
    async def encode_json(cls, content):
        return json.dumps(content, ensure_ascii=False)

    # При подключении клиента к WebSocket
    async def connect(self):
        try:
            self.user = self.scope["user"]

            # Если запрос на подключение пришел от неавторизованного пользователя
            if not(self.user.is_authenticated):
                await self.close(code=4001)
                return

            self.initialize_room_service()
            await self.accept()

        except Exception as ex:
            await self.close(code=1011)

    # При отключении клиента от WebSocket
    async def disconnect(self, code):
        try:

            # Если отключается владелец комнаты
            if await self.room_service.is_owner(self.room_uuid, self.participant_id):

                await self.room_service.delete_room(self.room_uuid)

                await self.send_everyone(
                    "chat_message",
                    str(self.participant_id),
                    "call_ended",
                    {
                        "reason": "owner_ended"
                    }
                )
            else:
                # Удаляем запись о consumer из RoomParticipantService
                await self.room_service.delete_participant(self.room_uuid, self.participant_id)

            # Удаляем текущего consumer из группы
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        except Exception as ex:
            return

    # Получаем сообщение от WebSocket
    async def receive_json(self, content, **kwargs):
        message_type = None

        try:
            content = content
            message_type = content["type"]

            match message_type:
                case WebSocketType.START_CALL.value:
                    await self.start_call()

                case WebSocketType.JOIN.value:
                    flag = await self.join()

                    # Уведомляем участников группы о том, что подключился новый пользователь
                    # (Только если подключение прошло успешно)
                    if (self.room_group_name is not None) and flag:

                        await self.send_everyone(
                            "chat_message",
                            str(self.participant_id),
                            "participant_joined",
                            {
                                "participant_id": str(self.participant_id),
                                "username": self.user.username,
                                "micro_muted": False,
                                "camera_enabled": False
                            }
                        )

                case WebSocketType.LEAVE.value:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))
                        return

                    # Уведомляем всех участников группы об отключении пользователя
                    await self.send_everyone(
                        "chat_message",
                        str(self.participant_id),
                        "participant_left",
                        {
                            "participant_id": str(self.participant_id)
                        }
                    )

                    await self.leave()

                case WebSocketType.END_CALL.value:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))
                        return

                    # Отключаем владельца комнаты
                    await self.end_call()

                case WebSocketType.OFFER.value:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))
                        return

                    to_participant_id = uuid.UUID(content["payload"]["to"])

                    # Проверяем, чтобы не было попытки установить соединение с самим собой
                    if self.participant_id == to_participant_id:
                        await self.send_json(self.json_error(4403, "Попытка установить соединение с самим собой", message_type))
                        return

                    # Проверяем, что отправитель и получатель состоят в одной комнате
                    if not(await self.room_service.is_consumers_in_same_room(self.room_uuid, self.participant_id, to_participant_id)):
                        await self.send_json(self.json_error(4400, "Пользователи не состоят в одной комнате", message_type))
                        return

                    # Отправляем offer конкретному пользователю
                    to_channel_name = await self.room_service.get_user_channel_name(self.room_uuid, to_participant_id)
                    await self.send_specific_consumer(
                        to_channel_name,
                        "chat_message",
                        WebSocketType.OFFER.value,
                        {
                            "from": str(self.participant_id),
                            "sdp": content['payload']['sdp']
                        }
                    )

                case WebSocketType.ANSWER.value:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))
                        return

                    to_participant_id = uuid.UUID(content["payload"]["to"])

                    # Проверяем, чтобы не было попытки установить соединение с самим собой
                    if self.participant_id == to_participant_id:
                        await self.send_json(
                            self.json_error(4403, "Попытка установить соединение с самим собой", message_type))
                        return

                    # Проверяем, что отправитель и получатель состоят в одной комнате
                    if not(await self.room_service.is_consumers_in_same_room(self.room_uuid, self.participant_id, to_participant_id)):
                        await self.send_json(self.json_error(4400, "Пользователи не состоят в одной комнате", message_type))
                        return

                    # Отправляем answer конкретному пользователю
                    to_channel_name = await self.room_service.get_user_channel_name(self.room_uuid, to_participant_id)
                    await self.send_specific_consumer(
                        to_channel_name,
                        "chat_message",
                        WebSocketType.ANSWER.value,
                        {
                            "from": str(self.participant_id),
                            "sdp": content['payload']['sdp']
                        }
                    )

                case WebSocketType.ICE_CANDIDATE.value:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))
                        return

                    to_participant_id = uuid.UUID(content["payload"]["to"])

                    # Проверяем, чтобы не было попытки установить соединение с самим собой
                    if self.participant_id == to_participant_id:
                        await self.send_json(
                            self.json_error(4403, "Попытка установить соединение с самим собой", message_type))
                        return

                    # Проверяем, что отправитель и получатель состоят в одной комнате
                    if not(await self.room_service.is_consumers_in_same_room(self.room_uuid, self.participant_id, to_participant_id)):
                        await self.send_json(self.json_error(4400, "Пользователи не состоят в одной комнате", message_type))
                        return

                    # Отправляем ice-candidate конкретному пользователю
                    to_channel_name = await self.room_service.get_user_channel_name(self.room_uuid, to_participant_id)
                    await self.send_specific_consumer(
                        to_channel_name,
                        "chat_message",
                        WebSocketType.ICE_CANDIDATE.value,
                        {
                            "to": str(to_participant_id),
                            "candidate": content['payload']['candidate']
                        }
                    )

                case WebSocketType.MUTE_CHANGED.value:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))
                        return

                    await self.room_service.set_micro_status(self.room_uuid, self.participant_id, content['payload']['muted'])
                    await self.send_everyone(
                        "chat_message",
                        str(self.participant_id),
                        "mute_changed",
                        {
                            "participant_id": str(self.participant_id),
                            "muted": bool(content['payload']['muted'])
                        }
                    )

                case WebSocketType.CAMERA_CHANGED.value:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))
                        return

                    await self.room_service.set_camera_status(self.room_uuid, self.participant_id, content['payload']['enabled'])
                    await self.send_everyone(
                        "chat_message",
                        str(self.participant_id),
                        "camera_changed",
                        {
                            "participant_id": str(self.participant_id),
                            "enabled": bool(content['payload']['enabled'])
                        }
                    )
                case _:
                    await self.send_json(self.json_error(4004, "Неизвестный тип запроса", message_type))

        except GroupException as ex:
            await self.send_json(self.json_error(ex.code, str(ex), message_type))

        except Exception as ex:
            await self.send_json(self.json_error(1011, "Произошла внутренняя ошибка сервера", message_type))

    # Владелец комнаты инициирует звонок
    async def start_call(self):
        try:

            room_uuid_temp = self.scope['url_route']['kwargs']['room_uuid']
            room_group_name_temp = f'room_{self.room_uuid}'

            self.participant_id = await self.room_service.add_owner(room_uuid_temp, self.user.id,
                                                                    self.channel_name, self.user.username)

            self.room_uuid = room_uuid_temp
            self.room_group_name = room_group_name_temp

            # Создаём группу и подключаемся к ней
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Отправляем первое сообщение с информацией о подключении
            await self.send_json({
                "type": "call_started"
            })

        except GroupException as ex:

            await self.send_json(self.json_error(ex.code, str(ex), WebSocketType.START_CALL.value))

        except Exception as ex:

            await self.send_json(self.json_error(1011, "Произошла внутренняя ошибка сервера", WebSocketType.START_CALL.value))

    # Пользователь желает присоединиться к комнате
    async def join(self):
        try:

            room_uuid_temp = self.scope['url_route']['kwargs']['room_uuid']
            room_group_name_temp = f'room_{self.room_uuid}'

            # Получаем информацию о тех, кто состоит в группе
            participants_array = await self.room_service.get_participants_by_room_id(room_uuid_temp)

            self.participant_id = await self.room_service.add_consumer(room_uuid_temp, self.user.id,
                                                                       self.channel_name, self.user.username)

            self.room_uuid = room_uuid_temp
            self.room_group_name = room_group_name_temp

            # Подключаемся к группе
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Отправляем первое сообщение с информацией о подключении
            await self.send_json({
                "type": "joined",
                "payload": {
                    "participant_id": str(self.participant_id),
                    "participants": participants_array
                }
            })

            return True

        except GroupException as ex:

            await self.send_json(self.json_error(ex.code, str(ex), WebSocketType.JOIN.value))
            return False

        except Exception as ex:

            await self.send_json(self.json_error(1011, "Произошла внутренняя ошибка сервера", WebSocketType.JOIN.value))
            return False

    async def leave(self):
        if not(await self.room_service.is_owner(self.room_uuid, self.participant_id)):
            await self.close()
            return
        else:
            await self.send_json(self.json_error(4003, "Отказано в доступе", WebSocketType.LEAVE.value))

    async def end_call(self):
        if await self.room_service.is_owner(self.room_uuid, self.participant_id):
            await self.close()
            return
        else:
            await self.send_json(self.json_error(4003, "Нет прав для завершения звонка", WebSocketType.END_CALL.value))

    # Метод для отправки сообщений всем участникам группы.
    # WebSocketType.EXCLUDED_PARTICIPANT_ID - participant_id того consumer,
    # которому не должно прийти сообщение от сервера.
    # Если excluded_participant_id = "", то сообщение должно быть доставлено всем участникам группы.
    async def send_everyone(self, method, excluded_participant_id, consumer_type, payload):

        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': method,
                WebSocketType.EXCLUDED_PARTICIPANT_ID.value: str(excluded_participant_id),
                WebSocketType.CONSUMER_TYPE.value: consumer_type,
                'payload': payload
            }
        )

    async def send_specific_consumer(self, channel_name, method, consumer_type, payload):

        # Метод отсылает сообщение не всем подключениям в группе, а только определенному участнику
        await self.channel_layer.send(
            channel_name,
            {
                'type': method,
                WebSocketType.CONSUMER_TYPE.value: consumer_type,
                'payload': payload
            }
        )

    async def chat_message(self, event):
        try:
            consumer_type = event[WebSocketType.CONSUMER_TYPE.value]
            payload = event['payload']

            if WebSocketType.EXCLUDED_PARTICIPANT_ID.value in event:
                excluded_participant_id = str(event[WebSocketType.EXCLUDED_PARTICIPANT_ID.value])
            else:
                excluded_participant_id = ""

            if len(excluded_participant_id) != 0:
                if str(self.participant_id) == excluded_participant_id: return

            match consumer_type:

                # Пришло указание на принудительное отключение вследствие выхода владельца комнаты
                case "call_ended":
                    await self.send_json({
                        'type': consumer_type,
                        'payload': payload
                    })

                    # Принудительно разрываем соединение
                    await self.close(4000)
                    return

                # Ответ клиенту по умолчанию
                case _:
                    await self.send_json({
                        'type': consumer_type,
                        'payload': payload
                    })

        except Exception as ex:
            await self.send_json(self.json_error(1011, "Произошла внутренняя ошибка сервера", "chat_message"))

    def json_error(self, code, message, request_type):
        return {
            "type": WebSocketType.ERROR.value,
            "payload": {
                "code": code,
                "message": message,
                "request_type": request_type
            }
        }
