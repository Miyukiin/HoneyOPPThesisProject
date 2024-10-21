from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        label=False, 
        max_length=50,  
        widget=forms.TextInput(
                attrs={'class': 'login-form-username', 
                       'placeholder': 'Username',
                }
        )
    )
    password = forms.CharField(
        label=False, 
        widget=forms.PasswordInput(
            attrs={
            'class': 'login-form-password',
            'placeholder': 'Password',
            }
        )
    )
    
class RegistrationForm(forms.Form):
    username = forms.CharField(
    label=False, 
    max_length=50,  
    widget=forms.TextInput(
            attrs={'class': 'register-form-username', 
                    'placeholder': 'Username',
            }
        )
    )
    password = forms.CharField(
        label=False, 
        widget=forms.PasswordInput(
            attrs={
            'class': 'register-form-password',
            'placeholder': 'Password',
            }
        )
    )