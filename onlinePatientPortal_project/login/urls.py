from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_user, name="login page"),
    path('register/', views.register_user, name="registration page"),
    path('logout/', views.greetings, name='logout page')
]
