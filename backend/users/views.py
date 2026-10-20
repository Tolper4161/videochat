from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse, JsonResponse
import json
import re

from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout

from users.models import User


# !!! ДОБАВИТЬ СОЗДАНЕИ НОВОЙ КОМНАТЫ ПРИ РЕГИСТРАЦИИ !!!
@require_http_methods(["POST"])
def save_user(request):
    try:

        # Проверяем, чтобы пользователь не был авторизован
        if (request.user.is_authenticated):
            return JsonResponse(
                {
                    "error": {
                        "code": "authenticated",
                        "message": "Пользователь уже авторизован"
                    }
                },
                status=403
            )

        data = json.loads(request.body)

        email = data["email"]
        username = data["username"]
        password = data["password"]

        # Проверяем, что почта соответствует шаблону example@example.example
        if not (is_correct_email(email)):
            return JsonResponse(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Переданные данные не прошли проверку",
                        "details": {
                            "email": [
                                "Почта не соответствует требованиям"
                            ]
                        }
                    }
                },
                status=422
            )

        # Проверяем, что длина пароля не менее 8 символов
        if (len(password) < 8):
            return JsonResponse(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Переданные данные не прошли проверку",
                        "details": {
                            "password": [
                                "Длина пароля должна быть не менее 8 символов"
                            ]
                        }
                    }
                },
                status=422
            )

        # Проверяем, что почта и username незаняты в системе
        users = User.objects.all()
        for user in users:
            if user.email == email:
                return JsonResponse(
                    {
                        "error": {
                            "code": "account_already_exists",
                            "message": "Пользователь с такими данными уже существует",
                            "details": {
                                "email": [
                                    "Этот email уже используется"
                                ]
                            }
                        }
                    },
                    status=409
                )

            if user.username == username:
                return JsonResponse(
                    {
                        "error": {
                            "code": "account_already_exists",
                            "message": "Пользователь с такими данными уже существует",
                            "details": {
                                "username": [
                                    "Это имя уже используется"
                                ]
                            }
                        }
                    },
                    status=409
                )

        new_user = User(
            email=email,
            username=username,
        )
        new_user.set_password(password)
        new_user.save()

        # Сразу после регистрации создаем сессию пользователя
        login(request, new_user)

        return JsonResponse({
            "id": new_user.id,
            "email": email,
            "username": username
        },
            status=201
        )

    except Exception as ex:
        return JsonResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Произошла внутренняя ошибка сервера"
                }
            },
            status=500
        )


@require_http_methods(["POST"])
def user_login(request):
    try:
        data = json.loads(request.body)
        email = data["email"]
        password = data["password"]

        # Проверяем, чтобы текущий пользователь не был авторизован
        if (request.user.is_authenticated):
            return JsonResponse(
                {
                    "error": {
                        "code": "authenticated",
                        "message": "Пользователь уже авторизован"
                    }
                },
                status=403
            )

        # Проверяем, что почта соответствует шаблону example@example.example
        if not (is_correct_email(email)):
            return JsonResponse(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Проверьте введенные данные",
                        "details": {
                            "email": [
                                "Укажите корректный email"
                            ]
                        }
                    }
                },
                status=422
            )

        # Аутентифицируем пользователя
        user = authenticate(request, username=email, password=password)

        # Если пароль неверный или логина не существует в БД
        if user is None:
            return JsonResponse(
                {
                    "error": {
                        "code": "invalid_credentials",
                        "message": "Введен неверный email или пароль"
                    }
                },
                status=401
            )
        # Создаем сессию для пользователя
        login(request, user)
        return HttpResponse(status=200)

    except Exception as ex:
        return JsonResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Произошла внутренняя ошибка сервера"
                }
            },
            status=500
        )


@require_http_methods(["POST"])
def user_logout(request):
    try:
        if not (request.user.is_authenticated):
            return JsonResponse(
                {
                    "error": {
                        "code": "not_authenticated",
                        "message": "Пользователь не авторизован"
                    }
                },
                status=401
            )

        # Аннулируем сессию текущего пользователя
        logout(request)
        return JsonResponse(
            {
                "message": "Выход выполнен"
            },
            status=200
        )

    except Exception as ex:
        return JsonResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Произошла внутренняя ошибка сервера"
                }
            },
            status=500
        )


# !!! Добавить удаление комнаты при удалении аккаунта!!!
@require_http_methods(["DELETE"])
def delete_user_by_id(request, user_id):
    try:
        current_user = request.user
        if not (current_user.is_authenticated):
            return JsonResponse(
                {
                    "error": {
                        "code": "not_authenticated",
                        "message": "Пользователь не авторизован"
                    }
                },
                status=401
            )

        # Проверяем, что запрос на удаление пользователя пришел именно от этого пользователя
        user_id = int(user_id)
        if (user_id != current_user.id):
            return JsonResponse(
                {
                    "error": {
                        "code": "forbidden",
                        "message": "Недостаточно прав"
                    }
                },
                status=403
            )

        if not (User.objects.filter(pk=user_id).exists()):
            return JsonResponse(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Переданные данные не прошли проверку",
                        "details": {
                            "id": [
                                "Не удалось удалить аккаунт"
                            ]
                        }
                    }
                },
                status=422
            )

        logout(request)
        current_user.delete()
        return JsonResponse(
            {
                "id": user_id,
                "email": current_user.email,
                "username": current_user.username
            },
            status=200
        )

    except Exception as ex:
        return JsonResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Произошла внутренняя ошибка сервера"
                }
            },
            status=500
        )


@require_http_methods(["GET"])
def get_user_data(request):
    try:
        current_user = request.user
        if not (current_user.is_authenticated):
            return JsonResponse(
                {
                    "error": {
                        "code": "not_authenticated",
                        "message": "Пользователь не авторизован"
                    }
                },
                status=401
            )

        return JsonResponse({
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username
        },
            status=200
        )

    except Exception as ex:
        return JsonResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Произошла внутренняя ошибка сервера"
                }
            },
            status=500
        )


@require_http_methods(["PATCH"])
def update_username(request):
    try:
        current_user = request.user
        if not (current_user.is_authenticated):
            return JsonResponse(
                {
                    "error": {
                        "code": "not_authenticated",
                        "message": "Пользователь не авторизован"
                    }
                },
                status=401
            )

        username = json.loads(request.body)["username"]

        # Проверяем, что username незанято в системе
        users = User.objects.all()
        for user in users:
            if user.username == username:
                return JsonResponse(
                    {
                        "error": {
                            "code": "username_already_exists",
                            "message": "Данное имя пользователя уже занято",
                            "details": {
                                "username": [
                                    "Выберите другое имя пользователя"
                                ]
                            }
                        }
                    },
                    status=409
                )

        User.objects.filter(pk=current_user.id).update(username=username)

        current_user.username = username
        return JsonResponse(
            {
                "id": current_user.id,
                "email": current_user.email,
                "username": username
            },
            status=200
        )

    except Exception as ex:
        return JsonResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Произошла внутренняя ошибка сервера"
                }
            },
            status=500
        )


@require_http_methods(["PATCH"])
def update_password(request):
    try:
        current_user = request.user
        if not (current_user.is_authenticated):
            return JsonResponse(
                {
                    "error": {
                        "code": "not_authenticated",
                        "message": "Пользователь не авторизован"
                    }
                },
                status=401
            )

        data = json.loads(request.body)
        old_password = data["old_password"]
        new_password = data["new_password"]

        if not (current_user.check_password(old_password)):
            return JsonResponse(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Переданные данные не прошли проверку",
                        "details": {
                            "old_password": [
                                "Неверные данные"
                            ]
                        }
                    }
                },
                status=422
            )

        # Проверяем, чтобы длина нового пароля была от 8 символов
        if (len(new_password) < 8):
            return JsonResponse(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Переданные данные не прошли проверку",
                        "details": {
                            "new_password": [
                                "Длина пароля должна быть не менее 8 символов"
                            ]
                        }
                    }
                },
                status=422
            )

        current_user.set_password(new_password)
        current_user.save()

        # Обновляем сессию, чтобы данные пользователя обновились на сервере и его не разлогинило
        update_session_auth_hash(request, current_user)

        return JsonResponse(
            {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.username
            },
            status=200
        )

    except Exception as ex:
        return JsonResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Произошла внутренняя ошибка сервера"
                }
            },
            status=500
        )


def is_correct_email(email):
    if (email.count('@') != 1): return False
    if (' ' in email): return False
    return re.fullmatch(".+@.+\\..+", email)