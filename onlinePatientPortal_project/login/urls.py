from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.redirect_view, name="redirect"),
    path("login/", views.login_view, name="login"),
    path('register/', views.register_view, name="register"),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
]
