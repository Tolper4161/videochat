from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from rooms.models import Room


@require_http_methods(["GET"])
def general(request):
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

        # Отправляем информацию о комнате
        room = Room.objects.filter(created_by=current_user).first()

        return JsonResponse(
            {
                "id": room.id,
                "title": room.title
            },
            status=200
        )

    except Exception as ex:
        return_internal_error()


def return_internal_error():
    return JsonResponse(
        {
            "error": {
                "code": "internal_error",
                "message": "Произошла внутренняя ошибка сервера"
            }
        },
        status=500
    )
