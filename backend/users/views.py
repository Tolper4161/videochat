from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
import json
import re

from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict

from users.models import User


@csrf_exempt  # ОБЯЗАТЕЛЬНО УБРАТЬ!!!
def save_user(request):
    # Нужно ли очищать данные от sql-инъекций и т.п.?
    try:
        data = json.loads(request.body)

        email = data["email"]
        username = data["username"]
        password = data["password"]

        # Проверяем, что почта соответствует шаблону example@aexample.example
        if not (is_correct_email(email)):
            return JsonResponse({"message": "Некорректная почта"}, status=400)

        # Проверяем, что почта и username незаняты в системе
        users = User.objects.all()
        for user in users:
            if user.email == email:
                return JsonResponse({"message": "Почта уже занята"}, status=400)

            if user.username == username:
                return JsonResponse({"message": "Имя уже занято"}, status=400)

        new_user = User(
            email=email,
            username=username,
        )
        new_user.set_password(password)
        new_user.save()

        return JsonResponse({"message": "Пользователь сохранен"}, status=200)

    except Exception as ex:
        return JsonResponse({"message": ex}, status=400)


@csrf_exempt  # ОБЯЗАТЕЛЬНО УБРАТЬ!!!
def delete_user_by_id(request, user_id):
    try:
        if not(request.user.is_authenticated):
            return JsonResponse({"message": f'Отклонено: для совершения действия в системе необходима авторизация'}, status=401)

        # Проверяем, что запрос на удаление пользователя пришел именно от этого пользователя
        current_user_to_delete = User.objects.get(id=int(user_id))

        if (current_user_to_delete.username != request.user.username):
            return JsonResponse({"message": f'Отклонено: нет доступа для совершения действия в системе'}, status=403)

        if not(User.objects.filter(pk=user_id).exists()):
            return JsonResponse({"message": f'Пользователя с id {user_id} нет в Базе Данных'}, status=400)

        current_user_to_delete.delete()
        return JsonResponse({"message": f'Пользователь с id {user_id} удален'}, status=200)

    except Exception as ex:
        return JsonResponse({"message": ex}, status=400)

@csrf_exempt  # ОБЯЗАТЕЛЬНО УБРАТЬ!!!
def get_user_data_by_id(request, user_id):
    try:
        if not (request.user.is_authenticated):
            return JsonResponse({"message": f'Отклонено: для совершения действия в системе необходима авторизация'}, status=401)

        current_user_to_data = User.objects.get(id=int(user_id))

        if current_user_to_data.username != request.user.username:
            return JsonResponse({"message": f'Отклонено: нет доступа для совершения действия в системе'}, status=403)

        response = model_to_dict(current_user_to_data)
        return JsonResponse(response)

    except Exception as ex:
        return JsonResponse({"message": ex}, status=400)


@csrf_exempt  # ОБЯЗАТЕЛЬНО УБРАТЬ!!!
def set_new_email(request):
    try:
        current_user = request.user
        if not (current_user.is_authenticated):
            return JsonResponse({"message": f'Отклонено: для совершения действия в системе необходима авторизация'}, status=401)

        current_username = current_user.username
        email = json.loads(request.body)["email"]

        # Проверяем, что почта незанята в системе
        users = User.objects.all()
        for user in users:
            if user.email == email:
                return JsonResponse({"message": "Почта уже занята"}, status=400)

        User.objects.filter(username=current_username).update(email=email)

        current_user.email = email
        response = model_to_dict(current_user)
        return JsonResponse(response)

    except Exception as ex:
        return JsonResponse({"message": ex}, status=400)


@csrf_exempt  # ОБЯЗАТЕЛЬНО УБРАТЬ!!!
def set_new_password(request):
    try:
        current_user = request.user
        if not(current_user.is_authenticated):
            return JsonResponse({"message": f'Отклонено: для совершения действия в системе необходима авторизация'}, status=401)

        data = json.loads(request.body)
        old_password = data["old_password"]
        new_password = data["new_password"]

        if not(current_user.check_password(old_password)):
            return JsonResponse({"message": f'Неверный текущий пароль'}, status=400)

        current_user.set_password(new_password)
        current_user.save()

        # Обновляем сессию, чтобы данные пользователя обновились на сервере и его не разлогинило
        update_session_auth_hash(request, current_user)

        response = model_to_dict(current_user)
        return JsonResponse(response)

    except Exception as ex:
        return JsonResponse({"message": ex}, status=400)


def is_correct_email(email):
    return re.fullmatch(".+@.+\\..+", email)
