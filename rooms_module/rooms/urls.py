from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import MyRoomView, RoomViewSet, InviteRoomView, JoinRequestDecisionView

router = DefaultRouter()
router.register("rooms", RoomViewSet, basename="room")
urlpatterns = [
    path("rooms/me/", MyRoomView.as_view(), name="my-room"),
    path("rooms/invite/<str:invite_code>/", InviteRoomView.as_view(), name="room-invite"),
    path("room-requests/<int:request_id>/<str:decision>/", JoinRequestDecisionView.as_view(), name="room-request-decision"),
    path("", include(router.urls)),
]
