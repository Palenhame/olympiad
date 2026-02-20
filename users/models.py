from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from tasks.models import Task


class UserRole(models.TextChoices):
    PLAYER = 'player', 'Игрок'
    STAFF = 'staff', 'Работник'
    ADMIN = 'admin', 'Администратор'


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PLAYER,
    )
    rating = models.IntegerField(default=100)
    solved_tasks = models.ManyToManyField(
        Task,
        related_name="solved_tasks",
        through='UserTask',
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username


class UserTask(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
