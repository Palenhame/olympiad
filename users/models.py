from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    PLAYER = 'player', 'Игрок'
    STAFF = 'staff', 'Работник'
    ADMIN = 'admin', 'Администратор'


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PLAYER,
    )
    rating = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
