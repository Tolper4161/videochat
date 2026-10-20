from django import forms
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from users.models import User


class CustomUserCreationForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "email")
