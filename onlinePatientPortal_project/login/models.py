from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser
import random
from django.contrib.auth import get_user_model

from django.conf import settings
from .utils import *

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **kwargs):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **kwargs) # Points to the associated CustomUser model and all its members.
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        
        if not username:
            raise ValueError('The Username field must be set')
        
        user = self.model(username=username, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = "CustomUser"  # Singular name
        verbose_name_plural = "CustomUsers"  # Correct plural name
        
    username = models.CharField(_("Username"), max_length=50, unique=True)
    email = models.EmailField(_("Email"), unique=True)
    password = models.CharField(_("Password"), max_length=128)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    last_modified = models.DateTimeField(_("Last Modified"), auto_now=True)
    random_index = models.IntegerField(_("Random Index"),unique=True, null=True, blank=True)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'username'
    
    def get_random_index(self):
        return self.random_index

    def save(self, *args, **kwargs):
        if self.random_index is None:
            self.random_index = self.generate_unique_random_index()
        super().save(*args, **kwargs)

    def generate_unique_random_index(self):
        while True:
            index = random.randint(1, 9999)
            if not CustomUser.objects.filter(random_index=index).exists():
                return index
            
    def get_username(self):
        return self.username

    def __str__(self):
        return self.username
    
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True
    
    @property
    def is_admin_user(self):
        return self.is_staff
    
class HoneyPasswords(models.Model):
    class Meta:
        verbose_name = "Honey Password"  # Singular name
        verbose_name_plural = "Honey Passwords"  # Correct plural name
        
    index = models.ForeignKey(settings.AUTH_USER_MODEL, to_field= 'random_index', verbose_name=_("User"), on_delete=models.CASCADE)
    honeyPasswords = models.JSONField(default=list)
    
    def __str__(self):
        honey_passwords_list = ', '.join([str(password) for password in self.honeyPasswords])
        return f"Honeypasswords for {self.index.username} are [{honey_passwords_list}]"


class UserInformation(models.Model):
    class Meta:
        verbose_name = "User Information"  # Singular name
        verbose_name_plural = "User Information"  # Correct plural name
    def __str__(self):
        return self.full_name
    
    index = models.ForeignKey(settings.AUTH_USER_MODEL, to_field= 'random_index', verbose_name=_("User"), on_delete=models.CASCADE)
    full_name = models.CharField(_("Full Name"), max_length=50, unique=False, blank= False, null= False)
    religion = models.CharField(_("Religion"), max_length=50, unique=False, blank= False, null= False)
    
    class SexChoices(models.TextChoices):
        MALE: tuple = 'M', 'Male'
        FEMALE: tuple = 'F', 'Female'
    class MaritalChoices(models.TextChoices):
        Single = 'Single'
        Married = 'Married'
        Widowed = 'Widowed'
        Separated = 'Separated'

    sex = models.CharField(
        _("Sex"),
        max_length=1,
        choices=SexChoices.choices,
        null= False,
        blank= False
    )
    marital_status = models.CharField(
        _("Marital Status"),
        max_length= 9,
        choices=MaritalChoices.choices,
        null= False,
        blank= False
    )
    date_of_birth = models.DateField(
        _("Date of Birth"),
        null= False,
        blank= False
    )
    social_security_number = models.CharField(
        _("Social Security Number"),
        max_length = 9,
        null= False,
        blank= False
    )
    address = models.CharField(_("Address"), max_length=50, unique=False, blank= False, null= False)
    country = models.CharField(_("Country"), max_length=50, unique=False, blank= False, null= False)
    province= models.CharField(_("Province"), max_length=50, unique=False, blank= False, null= False)
    city = models.CharField(_("City"), max_length=50, unique=False, blank= False, null= False)
    contact_number = models.CharField(_("Contact Number"), max_length=11, unique=False, blank= False, null= False)
    zip_code = models.CharField(_("Zip Code"), max_length=4, unique=False, blank= False, null= False)
    mother_name = models.CharField(_("Mother's Name"), max_length=50, unique=False, blank= False, null= False)