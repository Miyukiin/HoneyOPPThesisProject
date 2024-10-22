from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model

from . import models
from .Forms import *
from .utils import *


# Create your views here.

def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            print(username,password)
            user = authenticate(request, username=username, password=password)
            print(user)
            if user is not None:
                login(request, user)
                return redirect('/index/') 
            
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = LoginForm()
        
    return render(request, 'login.html', {'form': form}) 


def register_user(request):
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
                return redirect('/login/') 
    else:
        form = RegistrationForm()
        
    return render(request, 'register.html', {'form': form})


@login_required
def home_page(request): 
    username = request.user.get_username() if request.user.is_authenticated else "Guest"
    return render(request, 'index.html', {'username': username})


def logout_view(request):
    logout(request)
    return redirect('/login/') 