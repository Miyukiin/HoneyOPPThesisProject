from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import random
from .utils import PasswordGeneration

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user = self.model(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser):
    username = models.CharField(_("Username"), max_length=50, unique=True)
    password = models.CharField(_("Password"), max_length=50)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    last_modified = models.DateTimeField(_("Last Modified"), auto_now=True)
    random_index = models.IntegerField(_("Random Index"), unique=True, null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'

    def save(self, *args, **kwargs):
        if self.random_index is None:
            self.random_index = self.generate_unique_random_index()
        super().save(*args, **kwargs)

    def generate_unique_random_index(self):
        while True:
            index = random.randint(1, 9999)
            if not User.objects.filter(random_index=index).exists():
                return index
            
    def get_username(self):
        return self.username

    def __str__(self):
        return self.username
    
class HoneyPasswords(models.Model):
    index = models.ForeignKey(User, to_field= 'random_index', verbose_name=_("User"), on_delete=models.CASCADE)
    honeyPasswords = models.JSONField(default=list)
    
    def __str__(self):
        return f"Honeypasswords for {self.user.username} are {self.honeyPasswords}"