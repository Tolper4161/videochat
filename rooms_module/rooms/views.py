from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied, ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Room, RoomParticipant, RoomJoinRequest
from .serializers import RoomSerializer, RoomUpdateSerializer, ParticipantSerializer, JoinRoomSerializer, JoinRequestSerializer
from .services import ensure_creator, join_room, leave_room, decide_join_request

def translate_error(exc):
    if isinstance(exc, PermissionDenied):
        raise DRFPermissionDenied(str(exc))
    if isinstance(exc, ValidationError):
        raise DRFValidationError(getattr(exc, "messages", [str(exc)]))
    raise exc

class MyRoomView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        room = get_object_or_404(Room, creator=request.user)
        return Response(RoomSerializer(room, context={"request": request}).data)
    def post(self, request):
        room, created = Room.create_for_user(request.user)
        return Response(RoomSerializer(room, context={"request": request}).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class RoomViewSet(viewsets.GenericViewSet):
    queryset = Room.objects.select_related("creator").all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(RoomSerializer(room, context={"request": request}).data)

    def partial_update(self, request, pk=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            ensure_creator(request.user, room)
        except PermissionDenied as exc:
            translate_error(exc)
        serializer = RoomUpdateSerializer(room, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RoomSerializer(room, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            ensure_creator(request.user, room)
            room.start()
        except (PermissionDenied, ValidationError) as exc:
            translate_error(exc)
        return Response(RoomSerializer(room, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            ensure_creator(request.user, room)
            room.end()
            room.participants.filter(is_connected=True).update(is_connected=False)
        except (PermissionDenied, ValidationError) as exc:
            translate_error(exc)
        return Response(RoomSerializer(room, context={"request": request}).data)

    @action(detail=True, methods=["get"])
    def participants(self, request, pk=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(ParticipantSerializer(room.participants.filter(is_connected=True), many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def join(self, request, pk=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = JoinRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        try:
            participant, join_request = join_room(room, user=user, guest_name=serializer.validated_data.get("guest_name", ""))
        except (PermissionDenied, ValidationError) as exc:
            translate_error(exc)
        if join_request:
            return Response({"detail": "Заявка отправлена на подтверждение.", "request_id": join_request.pk,
                             "status": join_request.status}, status=status.HTTP_202_ACCEPTED)
        return Response(ParticipantSerializer(participant).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def leave(self, request, pk=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        participant_id = request.data.get("participant_id")
        participant = get_object_or_404(RoomParticipant, pk=participant_id, room=room, is_connected=True)
        if participant.user_id and (not request.user.is_authenticated or participant.user_id != request.user.pk):
            return Response({"detail": "Можно отключить только собственное подключение."}, status=status.HTTP_403_FORBIDDEN)
        leave_room(participant)
        return Response({"detail": "Вы вышли из комнаты."})

    @action(detail=True, methods=["delete"], url_path=r"participants/(?P<participant_id>[^/.]+)")
    def remove_participant(self, request, pk=None, participant_id=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            ensure_creator(request.user, room)
        except PermissionDenied as exc:
            translate_error(exc)
        participant = get_object_or_404(RoomParticipant, pk=participant_id, room=room)
        participant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def requests(self, request, pk=None):
        room = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            ensure_creator(request.user, room)
        except PermissionDenied as exc:
            translate_error(exc)
        return Response(JoinRequestSerializer(room.join_requests.all(), many=True).data)

class InviteRoomView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, invite_code):
        room = get_object_or_404(Room, invite_code=invite_code)
        return Response(RoomSerializer(room, context={"request": request}).data)

class JoinRequestDecisionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, request_id, decision):
        if decision not in ("approve", "reject"):
            return Response({"detail": "Решение должно быть approve или reject."}, status=400)
        join_request = get_object_or_404(RoomJoinRequest.objects.select_related("room"), pk=request_id)
        try:
            ensure_creator(request.user, join_request.room)
            participant = decide_join_request(join_request, approved=(decision == "approve"))
        except (PermissionDenied, ValidationError) as exc:
            translate_error(exc)
        result = {"status": join_request.status}
        if participant:
            result["participant"] = ParticipantSerializer(participant).data
        return Response(result)
