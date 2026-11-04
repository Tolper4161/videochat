from channels.generic.websocket import AsyncJsonWebsocketConsumer

from signaling.models import RoomPermissionsService, GroupException
from ws_types import WebSocketType
import json

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
        if cls.room_service is None: cls.room_service = RoomPermissionsService()

    # При подключении клиента к WebSocket
    async def connect(self):
        try:
            self.user = self.scope["user"]

            # Если запрос на подключение пришел от неавторизованного пользователя
            if not(self.user.is_authenticated()):
                await self.close(code=4001)
                return

            self.initialize_room_service()
            await self.accept()

        except Exception as ex:
            await self.close(code=1011)

    # При отключении клиента от WebSocket
    async def disconnect(self, code):
        try:
            # Удаляем текущего consumer из группы
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            # Удаляем запись о consumer из RoomPermissionsService
            await self.room_service.delete_participant(self.room_uuid, self.participant_id)

            # Если отключается владелец комнаты
            if await self.room_service.is_owner(self.room_uuid, self.participant_id):
                await self.room_service.delete_room(self.room_uuid)

                await self.send_everyone(
                    "chat_message",
                    "call_ended",
                    {
                        "reason": "owner_ended"
                    }
                )

        except Exception as ex:
            return

    # Получаем сообщение от WebSocket
    async def receive_json(self, content, **kwargs):
        message_type = None

        try:
            data = json.loads(content)
            message_type = data["type"]

            match message_type:
                case WebSocketType.START_CALL:
                    await self.start_call()

                case WebSocketType.JOIN:
                    await self.join()

                    # Уведомляем участников группы о том, что подключился новый пользователь
                    await self.send_everyone(
                        "chat_message",
                        "participant_joined",
                        {
                            "participant_id": self.participant_id,
                            "username": self.user.username,
                            "micro_muted": False,
                            "camera_enabled": False
                        }
                    )

                case WebSocketType.LEAVE:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))

                    # Уведомляем всех участников группы об отключении пользователя
                    await self.send_everyone(
                        "chat_message",
                        "participant_left",
                        {
                            "participant_id": self.participant_id
                        }
                    )

                    await self.leave()

                case WebSocketType.END_CALL:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))

                    # Отключаем владельца комнаты
                    await self.end_call()

                case WebSocketType.OFFER:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))

                    await self.send_everyone(
                        "chat_message",
                        WebSocketType.OFFER,
                        {
                            "from": self.participant_id,
                            "sdp": data['payload']['sdp']
                        }
                    )

                case WebSocketType.ANSWER:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))

                    await self.send_everyone(
                        "chat_message",
                        WebSocketType.ANSWER,
                        {
                            "from": self.participant_id,
                            "sdp": data['payload']['sdp']
                        }
                    )

                case WebSocketType.ICE_CANDIDATE:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))

                    await self.send_everyone(
                        "chat_message",
                        WebSocketType.ICE_CANDIDATE,
                        data['payload']
                    )

                case WebSocketType.MUTE_CHANGED:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))

                    await self.send_everyone(
                        "chat_message",
                        "mute_changed",
                        {
                            "participant_id": self.participant_id,
                            "muted": bool(data['payload']['muted'])
                        }
                    )

                case WebSocketType.CAMERA_CHANGED:
                    if self.participant_id is None:
                        await self.send_json(self.json_error(4400, "Пользователь не состоит ни в одной комнате", message_type))

                    await self.send_everyone(
                        "chat_message",
                        "camera_changed",
                        {
                            "participant_id": self.participant_id,
                            "enabled": bool(data['payload']['enabled'])
                        }
                    )

        except Exception as ex:
            await self.send_json(self.json_error(1011, "Произошла внутренняя ошибка сервера", message_type))

    # Владелец комнаты инициирует звонок
    async def start_call(self):
        try:
            self.room_uuid = self.scope['url_route']['kwargs']['room_uuid']
            self.room_group_name = f'room_{self.room_uuid}'

            self.participant_id = await self.room_service.add_owner(self.room_uuid, self.user.id)

            # Создаём группу и подключаемся к ней
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Отправляем первое сообщение с информацией о подключении
            await self.send_json(self, {
                "type": "call_started"
            })

        except GroupException as ex:
            self.room_uuid = None
            self.room_group_name = None
            self.participant_id = None

            await self.send_json(self.json_error(ex.code, str(ex), WebSocketType.START_CALL))

        except Exception as ex:
            self.room_uuid = None
            self.room_group_name = None
            self.participant_id = None

            await self.send_json(self.json_error(1011, "Произошла внутренняя ошибка сервера", WebSocketType.START_CALL))

    # Пользователь желает присоединиться к комнате
    async def join(self):
        try:
            self.room_uuid = self.scope['url_route']['kwargs']['room_uuid']
            self.room_group_name = f'room_{self.room_uuid}'

            self.participant_id = await self.room_service.add_consumer(self.room_uuid, self.user.id)

            # Подключаемся к группе
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Отправляем первое сообщение с информацией о подключении
            await self.send_json(self, {
                "type": "joined",
                "payload": {
                    "participant_id": self.participant_id,
                    "participants": [
                        {
                            "username": self.user.username,
                            "participant_id": self.participant_id,
                            "micro_muted": False,
                            "camera_enabled": False
                        }
                    ]
                }
            })

        except GroupException as ex:
            self.room_uuid = None
            self.room_group_name = None
            self.participant_id = None

            await self.send_json(self.json_error(ex.code, str(ex), WebSocketType.JOIN))

        except Exception as ex:
            self.room_uuid = None
            self.room_group_name = None
            self.participant_id = None

            await self.send_json(self.json_error(1011, "Произошла внутренняя ошибка сервера", WebSocketType.JOIN))

    async def leave(self):
        if not(await self.room_service.is_owner(self.room_uuid, self.participant_id)):
            await self.close()
            return
        else:
            await self.send_json(self.json_error(4003, "Отказано в доступе", WebSocketType.LEAVE))

    async def end_call(self):
        if await self.room_service.is_owner(self.room_uuid, self.participant_id):
            await self.close()
            return
        else:
            await self.send_json(self.json_error(4003, "Нет прав для завершения звонка", WebSocketType.END_CALL))

    # Метод для отправки сообщений всем участникам группы
    async def send_everyone(self, method, consumer_type, payload):

        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': method,
                WebSocketType.CONSUMER_TYPE: consumer_type,
                'payload': payload
            }
        )

    async def chat_message(self, event):
        try:
            consumer_type = event[WebSocketType.CONSUMER_TYPE]
            payload = event['payload']

            match consumer_type:

                # Пришло указание на принудительное отключение вследствие выхода владельца комнаты
                case "call_ended":
                    await self.send_json({
                        'type': consumer_type,
                        'payload': payload
                    })

                    # Принудительно разрываем соединение
                    await self.close(1001)
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
            "type": WebSocketType.ERROR,
            "payload": {
                "code": code,
                "message": message,
                "request_type": request_type
            }
        }
