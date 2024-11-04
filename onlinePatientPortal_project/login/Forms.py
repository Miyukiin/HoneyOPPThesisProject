from django import forms
from login.models import CustomUser, UserInformation

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
    email = forms.EmailField(
        label=False,
        widget=forms.EmailInput(
            attrs={
            'class': 'register-form-email',
            'placeholder': 'Email',
            }
        )
    )
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
    confirm_password = forms.CharField(
        label=False, 
        widget=forms.PasswordInput(
            attrs={
            'class': 'register-form-password',
            'placeholder': 'Confirm Your Password',
            }
        )
    )

class UserInformationForm(forms.ModelForm):
    class Meta:
        model = UserInformation
        fields = '__all__'
        exclude = ['index']
    def __init__(self, *args, **kwargs):
        super(UserInformationForm, self).__init__(*args, **kwargs)
        # Make all fields read-only by disabling them
        for field in self.fields.values():
            field.widget.attrs['readonly'] = True  # Make fields read-only
            field.widget.attrs['disabled'] = True  # Disable fields for further protection
    """  
    widgets = {
        'full_name': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'religion': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'sex': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'marital_status': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'date_of_birth': forms.DateInput(attrs={'class': 'custom-form-class'}),
        'social_security_number': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'address': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'country': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'province': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'city': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'contact_number': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'zip_code': forms.TextInput(attrs={'class': 'custom-form-class'}),
        'mother_name': forms.TextInput(attrs={'class': 'custom-form-class'}),
    }
    """ 