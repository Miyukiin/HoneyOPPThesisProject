from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from login.models import CustomUser

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(UserGeneralInformation)
admin.site.register(UserMedicalInformation)
admin.site.register(HoneyPasswords)
