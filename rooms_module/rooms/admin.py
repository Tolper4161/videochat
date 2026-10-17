from django.contrib import admin
from .models import Room, RoomParticipant, RoomJoinRequest

class RoomParticipantInline(admin.TabularInline):
    model = RoomParticipant
    extra = 0

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "creator", "status", "is_private", "created_at")
    list_filter = ("status", "is_private", "allow_guests")
    search_fields = ("name", "creator__username", "invite_code")
    inlines = [RoomParticipantInline]

@admin.register(RoomJoinRequest)
class RoomJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("room", "guest_name", "user", "status", "created_at")
    list_filter = ("status",)
