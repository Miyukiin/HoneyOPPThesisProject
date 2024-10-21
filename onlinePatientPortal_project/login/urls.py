from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_user, name="login page"),
    path('register/', views.register_user, name="registration page"),
    path('greetings/', views.greetings, name='results page'),
]
