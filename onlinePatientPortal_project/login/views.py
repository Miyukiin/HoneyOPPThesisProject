from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model
from rest_framework.decorators import api_view

from .models import *
from .forms import *
from .utils import *


# Create your views here.
def login_view(request: HttpRequest):
    context = {}
    if request.user.is_authenticated:
        dashboard_view(request)
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        context['form'] = form
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username, password=password)
            # If there is a user with this username.
            if user is not None:
                login(request, user) 
                request.session['user_password'] = password # Store for dashboard_view purposes
                
                # If Genuine user then Lead to Genuine Environment
                if getattr(user, 'is_genuine', False):
                    request.session['is_genuine'] = True  # Custom attribute stored in the session
                else: # Else Lead to Fictitious Environment
                    request.session['is_genuine'] = False  # Custom attribute stored in the session
                    
                return redirect(reverse('dashboard'))
            
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = LoginForm()
        context['form'] = form
        
    return render(request, 'login.html', context) 


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
    is_genuine = request.session.get('is_genuine', False)  # Retrieve or default to False
    username = request.user.get_username()
    
    try:
        user = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        user = None  # Handle the case where the user is not found
    except get_user_model().MultipleObjectsReturned:
        user = None  # Handle the case where multiple users are found

    if is_genuine:
        if user:
            try:
                # Use the relationship to query UserInformation
                user_general_info_object = UserGeneralInformation.objects.get(index=user.get_random_index())
                #user_medical_info_object = UserMedicalInformation.objects.get(index=user.get_random_index())
            except UserGeneralInformation.DoesNotExist or UserMedicalInformation.DoesNotExist:
                raise Exception(f"Unable to query User Information for {user}")
            
        if  user_general_info_object: #and user_medical_info_object:
            general_form = UserGeneralInformationForm(instance=user_general_info_object)
            #medical_form = UserMedicalInformationForm(instance=user_medical_info_object)
            user_full_name = " ".join([user_general_info_object.first_name,user_general_info_object.middle_name,user_general_info_object.last_name])
        else:
            general_form = UserGeneralInformationForm()
            #medical_form = UserMedicalInformationForm()
            user_full_name = 'None'
            
        context = {
            'user_full_name': user_full_name,
            'general_form': general_form,
            #'medical_form': medical_form,
            'environment': "Genuine" 
        }
    else: # Fictitious Environment. Plug logic for fake data here.
        # Hash Password
        try:
            honeypassword_hasher_api_url = 'http://127.0.0.1:8002/honeypassword/hash_honeypasswords/'
            honey_password_query = HoneyPasswords.objects.get(index= user)
            data = {
                "honeyword_list": [request.session.get('user_password')], 
                "salt": honey_password_query.salt
            }
            
            try:
                response = requests.post(honeypassword_hasher_api_url, json=data)  # Call API with honeywordlist as honeywords
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to send data to the honeypassword hasher API: {str(e)}")
            
            response_text = response.json()
            honeyhash_list:list[str] = response_text['honeyword_hashes'] 
            
        except Exception as e:
                # Return error response
                return JsonResponse({"error": f"Unable to hash honeypasswords: {str(e)}"}, status=500)
            
        # Decrypt DTE Seed
        try:
            honeydecrypt_seed_api_url = 'http://127.0.0.1:8002/honeydistributive/decrypt_dte_seeds/'  # Adjust URL as needed
            seed_query = EncryptedSeed.objects.get(index = user)

            data = {
                'rbmrsa_parameters': seed_query.rbmrsa_parameters,
                'password_hash': honeyhash_list[0],
                'encrypted_seed': seed_query.ciphertext,
            }
            
            try:
                response = requests.post(honeydecrypt_seed_api_url, json=data) # Call API
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to send data to the honeygenerator API: {str(e)}")
            
            response_text = response.json()
            dte_seeds = response_text['dte_seeds']
            
        except Exception as e:
            # Return error response
            return JsonResponse({"error": f"Unable to decrypt dte seed: {str(e)}"}, status=500)
        
        # Decode DTE Seed to Messages
        try:
            honeydtedecode_seed_api_url = 'http://127.0.0.1:8002/honeydistributive/decode_dte_seeds/'  # Adjust URL as needed

            data = {
                "dte_seeds": dte_seeds
            }
            try:
                response = requests.get(honeydtedecode_seed_api_url, json=data) # Call API
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to send data to the honeygenerator API: {str(e)}")
            
            response_text = response.json()
            field_message_dict = response_text['field_message_dict']
            
        except Exception as e:
            # Return error response
            return JsonResponse({"error": f"Unable to decode dte seed: {str(e)}"}, status=500)
        
        try:
            # Use the relationship to query UserInformation
            user_general_info_object = UserGeneralInformation.objects.get(index=user.get_random_index())
        except UserGeneralInformation.DoesNotExist or UserMedicalInformation.DoesNotExist:
            raise Exception(f"Unable to query User Information for {user}")
              
        if user_general_info_object:# and user_medical_info_object:
            user_full_name = " ".join([field_message_dict.get('firstnames'),field_message_dict.get('middlenames'),field_message_dict.get('lastnames')])
            # Instead of binding real data, plug fake data as initial
            general_form = UserGeneralInformationForm(
                instance=user_general_info_object,  # real data
                initial={
                    # only override the fields with fake values
                    'first_name': field_message_dict.get('firstnames'),
                    'middle_name': field_message_dict.get('middlenames'),
                    'last_name': field_message_dict.get('lastnames'),
                    'birth_date': field_message_dict.get('birthdate'),
                    'nationality': field_message_dict.get('nationality'),
                    'civil_status': field_message_dict.get('maritalstatus'),
                    'philID': field_message_dict.get('philid'),
                    'sss_number': field_message_dict.get('sssNo'),
                    'sex': field_message_dict.get('sex'),
                    'suffix_name': field_message_dict.get('suffixes'),
                    'passport_number': field_message_dict.get('passportNo'),
                    'religion': field_message_dict.get('religion'),
                    'occupation': field_message_dict.get('occupation'),
                }
            )
        else:
            general_form = UserGeneralInformationForm()
            #medical_form = UserMedicalInformationForm()
            user_full_name = 'None'
            
        context = {
            'user_full_name': user_full_name,
            'general_form': general_form,
            #'medical_form': medical_form,
            'environment': "Fictitious" 
        }
        
    return render(request, 'index.html', context)

@login_required
def logout_view(request:HttpRequest):
    logout(request)
    return redirect(reverse('login'))