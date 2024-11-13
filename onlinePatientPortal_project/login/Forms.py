from django import forms
from login.models import CustomUser, UserGeneralInformation, UserMedicalInformation

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

class UserGeneralInformationForm(forms.ModelForm):
    class Meta:
        model = UserGeneralInformation
        fields = '__all__'
        exclude = ['index']
        widgets = {
            'isAmericanIndian': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isAsian': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isBlack': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isHispanic': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isWhite': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isNativeHawaiian': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isChild': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isNonLocal': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isHospitalEmp': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isNoPersonalDataRelease': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isNoCompanyCommunication': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isFictitiousBirthDate': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
            'isConfidentialPatientRecord': forms.CheckboxInput(attrs={'class': 'checkbox-class'}),
        }
        
    first_column_fields = []
    second_column_fields = []
    
    def __init__(self, *args, **kwargs):
        super(UserGeneralInformationForm, self).__init__(*args, **kwargs)
        
        self.first_column_fields = [self[field] for field in [
            'first_name', 'middle_name', 'last_name', 'suffix_name', 'civil_status', 'sex', 'nationality', 
            'religion', 'philID', 'sss_number', 'passport_number', 'citizenship', 'company', 
            'company_address', 'occupation'
        ]]
        
        self.second_column_fields = [self[field] for field in [
            'birth_date', 'isFictitiousBirthDate', 'age', 'remarks', 'isAmericanIndian', 'isAsian', 
            'isBlack', 'isHispanic', 'isWhite', 'isNativeHawaiian', 'isChild', 'isNonLocal', 
            'isHospitalEmp', 'isNoPersonalDataRelease', 'isNoCompanyCommunication', 
            'isConfidentialPatientRecord'
        ]]

        for field in self.fields.values():
            field.widget.attrs['readonly'] = True  
            field.widget.attrs['disabled'] = True  
            if field.widget.input_type == "checkbox":
                 field.label_suffix = ''

class UserMedicalInformationForm(forms.ModelForm):
    class Meta:
        model = UserMedicalInformation
        fields = '__all__'
        exclude = ['index']
    def __init__(self, *args, **kwargs):
        super(UserMedicalInformationForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['readonly'] = True  
            field.widget.attrs['disabled'] = True  