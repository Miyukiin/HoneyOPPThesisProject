from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from login.models import CustomUser

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(HoneyPasswords)
admin.site.register(UserInformation)
