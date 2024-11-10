from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
import requests
from .models import HoneyPasswords

class HoneywordBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        User = get_user_model()
        try:
            user:object = User.objects.get(username=username)
            hp_query:object = HoneyPasswords.objects.get(index_id=user.random_index)
            password_list:list = hp_query.honeyPasswords
            
            api_url = 'http://127.0.0.1:8001/api/verify/' # LocalHost of api service running on port 8001 in the specified url.
            data = {
                'user_index': user.random_index,
                'password_candidate': password,
                'password_list': password_list
            }
            
            try:
                response = requests.post(api_url, json=data) # Call API
                response.raise_for_status() # Raises HTTPError for bad status codes
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to connect to verification service: {str(e)}")
            
            if response.status_code == 200:
                result = response.json()
                if result == {'status': 'success', 'isCorrect': True, 'isHoneyword': True, 'isSugarword': False}: 
                    user.is_genuine = False # Fictitious result
                    return user
                elif result == {'status': 'success', 'isCorrect': True, 'isHoneyword': True, 'isSugarword': True}:
                    user.is_genuine = True # Genuine reuslt
                    return user
                else:
                    return None  # Invalid password, failed authentication

        except (User.DoesNotExist, HoneyPasswords.DoesNotExist):
            return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None