from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model

from .models import *
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
    try:
        user = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        user = None  # Handle the case where the user is not found
    except get_user_model().MultipleObjectsReturned:
        user = None  # Handle the case where multiple users are found

    if user:
        try:
            # Use the foreign key relationship to query UserInformation
            userinfo_object = UserInformation.objects.get(index=user.get_random_index())
        except UserInformation.DoesNotExist:
            raise Exception(f"Unable to query User Information for {user}")
        
    if userinfo_object:
        form = UserInformationForm(instance=userinfo_object)
    else:
        form = UserInformationForm()
        
    context = {
        'username': username,
        'form': form 
    }
    return render(request, 'index.html', context)

@login_required
def logout_view(request:HttpRequest):
    logout(request)
    return redirect(reverse('login'))