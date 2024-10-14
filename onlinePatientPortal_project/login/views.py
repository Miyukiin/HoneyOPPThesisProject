from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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
            
            # Manually checking the username and password
            try:
                user = models.User.objects.get(username=username, password=password)
                login(request, user)  # Use Django's login method to log the user in
                messages.success(request, "Login successful! Redirecting")
                return redirect('logout/') 
            except models.User.DoesNotExist:
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
            new_user = models.User(username=username)
            new_user.password = password
            new_user.save()
            messages.success(request, "Registration successful! You can now log in.")
            
        return redirect('login/') 
    else:
        form = RegistrationForm()
        
    return render(request, 'register.html', {'form': form})

@login_required
def greetings(request): 
    if request.user.is_authenticated:
        username = request.user.get_username()
    else:
        username = "Guest"
    return render(request, 'logout.html', {'username': username})
        