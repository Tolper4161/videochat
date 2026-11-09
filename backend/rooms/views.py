from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

import json
from rooms.models import Room


@require_http_methods(["GET"])
def get_room_general(request):
    try:
        if not (request.user.is_authenticated):
            return JsonResponse(
                {"error": {"code": "not_authenticated", "message": "Требуется авторизация"}},
                status=401
            )

        try:
            room = Room.objects.get(created_by=request.user)
            return JsonResponse({
                "id": str(room.id),
                "title": room.title
            }, status=200)
        except Room.DoesNotExist:
            return JsonResponse(
                {"error": {"code": "not_found", "message": "Комната для данного пользователя не найдена"}},
                status=404
            )

    except Exception as ex:
        return JsonResponse({"error": {"code": "internal_error", "message": "Произошла внутренняя ошибка сервера"}},
                            status=500)


@require_http_methods(["PATCH"])
def update_room_title(request):
    try:
        if not (request.user.is_authenticated):
            return JsonResponse(
                {"error": {"code": "not_authenticated", "message": "Требуется авторизация"}},
                status=401
            )

        data = json.loads(request.body)
        title = data.get("title", "").strip()

        if not title:
            return JsonResponse(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Переданные данные не прошли проверку",
                        "details": {"username": "Название комнаты не может быть пустым"}
                    }
                },
                status=422
            )

        try:
            room = Room.objects.get(created_by=request.user)
            room.title = title
            room.save()

            return JsonResponse({
                "id": str(room.id),
                "title": room.title
            }, status=200)
        except Room.DoesNotExist:
            return JsonResponse(
                {"error": {"code": "not_found", "message": "Комната для данного пользователя не найдена"}},
                status=404
            )

    except Exception as ex:
        return JsonResponse({"error": {"code": "internal_error", "message": "Произошла внутренняя ошибка сервера"}},
                            status=500)
