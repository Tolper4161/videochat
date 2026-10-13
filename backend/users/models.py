from django.contrib.auth.models import AbstractUser
from django.db import models

# Добавить в admin.py эту модель, чтобы она в админ панели отображалась
class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=255, blank=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

def __str__(self):
        return f'{self.email} {self.username}'
