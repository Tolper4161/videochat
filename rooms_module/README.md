# Модуль ROOM — Django

Самостоятельное демонстрационное приложение для управления комнатами видеочата: модели, REST API, базовая бизнес-логика, права доступа, админка и тесты.

## Реализовано

- Одна постоянная комната на зарегистрированного пользователя.
- Автоматическое название по имени пользователя; при совпадении добавляется номер.
- Уникальный код приглашения.
- Статусы `inactive`, `active`, `ended`.
- Переименование неактивной комнаты и настройки приватности/гостевого входа.
- Список участников, вход/выход и удаление участника создателем.
- Гостевой вход без аккаунта.
- Заявки на вход и решение создателя.
- Django Admin и базовые автоматические тесты.

## Ограничения текущей версии

Это демонстрационный модуль управления комнатами, а не законченная видеосвязь. WebRTC, передача аудио/видео, WebSocket-события, фронтенд и production-аутентификация не включены. Гостевой вход сейчас принимает имя из запроса; перед реальным развёртыванием нужно привязать гостя к подписанной сессии/токену, чтобы нельзя было выдавать себя за другого участника. В production также нужны защищённый `SECRET_KEY`, HTTPS, корректная настройка CSRF/CORS и выбранный командой механизм аутентификации.

## Запуск на macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API: `http://127.0.0.1:8000/api/`. В демо используются SQLite и стандартная модель пользователя Django.

## Основные эндпоинты

| Метод | URL | Назначение |
|---|---|---|
| `POST` | `/api/rooms/me/` | Создать комнату или вернуть существующую |
| `GET` | `/api/rooms/me/` | Получить свою комнату |
| `GET` | `/api/rooms/{id}/` | Получить комнату |
| `PATCH` | `/api/rooms/{id}/` | Изменить название/настройки (создатель) |
| `POST` | `/api/rooms/{id}/start/` | Начать звонок |
| `POST` | `/api/rooms/{id}/end/` | Завершить звонок |
| `POST` | `/api/rooms/{id}/join/` | Подключиться или подать заявку |
| `POST` | `/api/rooms/{id}/leave/` | Отключить своё подключение по `participant_id` |
| `GET` | `/api/rooms/{id}/participants/` | Получить подключённых участников |
| `DELETE` | `/api/rooms/{id}/participants/{participant_id}/` | Удалить участника (создатель) |
| `GET` | `/api/rooms/{id}/requests/` | Список заявок (создатель) |
| `POST` | `/api/room-requests/{request_id}/approve/` | Одобрить заявку |
| `POST` | `/api/room-requests/{request_id}/reject/` | Отклонить заявку |
| `GET` | `/api/rooms/invite/{invite_code}/` | Получить комнату по коду приглашения |

## Примеры

Создать комнату (нужна авторизация):
```bash
curl -u alice:password -X POST http://127.0.0.1:8000/api/rooms/me/
```

Переименовать:
```bash
curl -u alice:password -X PATCH http://127.0.0.1:8000/api/rooms/1/ \
  -H 'Content-Type: application/json' -d '{"name":"Рабочая встреча"}'
```

Гостевой вход в публичную комнату:
```bash
curl -X POST http://127.0.0.1:8000/api/rooms/1/join/ \
  -H 'Content-Type: application/json' -d '{"guest_name":"Гость"}'
```

## Тесты

```bash
python manage.py test rooms
```

## Подключение к общему проекту

1. Скопировать каталог `rooms/` в корень Django-проекта.
2. Добавить `"rooms"` и `"rest_framework"` в `INSTALLED_APPS`.
3. Подключить `path("api/", include("rooms.urls"))` в корневом `urls.py`.
4. Проверить, что проект использует `settings.AUTH_USER_MODEL`.
5. Выполнить `python manage.py makemigrations rooms` и `python manage.py migrate`.
6. Согласовать API-контракт и способ аутентификации с командой.

## Что стоит согласовать перед production

- PostgreSQL и тесты на конкурентное создание комнаты.
- Нужно ли возвращать статус в `inactive` после звонка или сохранять `ended`.
- Подписанные токены гостевых участников.
- WebSocket/Channels и перечень событий после согласования с фронтендом.
- Истечение/отзыв ссылок и хранение истории участников.
