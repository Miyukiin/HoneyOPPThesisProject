from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model

from . import models
from .Forms import *
from .utils import *


# Create your views here.

def login_view(request: HttpRequest):
    if request.user.is_authenticated:
        dashboard_view(request)
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(reverse('dashboard'))
            
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = LoginForm()
        
    return render(request, 'login.html', {'form': form}) 


def register_view(request:HttpRequest):
    if request.user.is_authenticated:
        dashboard_view(request)
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
    
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            
            if get_user_model().objects.filter(username=username).exists():
                form.add_error('username', "Username already used.")
            if get_user_model().objects.filter(email=email).exists():
                form.add_error('email', "Email already used.")
                
            if not form.errors:
                user = get_user_model().objects.create_user(
                    username=username, 
                    email=email, 
                    password=password
                )
                return redirect(reverse('login'))
    else:
        form = RegistrationForm()
        
    return render(request, 'register.html', {'form': form})

def redirect_view(request:HttpRequest):
    if request.user.is_authenticated:
        return redirect(reverse('dashboard'))
    else:
        return redirect(reverse('login'))

@login_required
def dashboard_view(request:HttpRequest): 
    username = request.user.get_username()
    return render(request, 'index.html', {'username': username})

@login_required
def logout_view(request:HttpRequest):
    logout(request)
    return redirect(reverse('login'))