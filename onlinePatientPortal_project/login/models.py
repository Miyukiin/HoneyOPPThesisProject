from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser
import random
from django.contrib.auth import get_user_model
import requests
from .static.models_resources import AllNationalities, AllReligion

from django.conf import settings
from .utils import ExistingPasswordGeneration, ProposedPasswordGeneration, MLHoneywordGenerator

# Create your models here.
class CustomUserManager(BaseUserManager):
    # from django.contrib.auth import get_user_model
    #  user = get_user_model().objects.create_user(username=username, email=email, password=password)
    def create_user(self, username, password=None, **kwargs):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **kwargs) # Creates an instance by pointing to the associated CustomUser model and all its members.
        
        # Create User, Create HoneyPasswords Entry, Create HoneyPassword API Check Entry
        user.save(using=self._db)
        
        # Create a HoneyPasswords entry after the user is created
        
        honeypassword_generator_api_url = 'http://127.0.0.1:8002/honeypassword/generate_honeypasswords/'
        
        data = {
            'password': password
        }
        
        try:
            response = requests.get(honeypassword_generator_api_url, params=data)  # Call API with password as a query parameter
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send data to the honeypassword generator API: {str(e)}")

        try:
            # Parse the response as JSON
            response_text = response.json()  # Convert response text to a dictionary
            honeyword_list = response_text['honeyword_list'] 
            sugarword_index = response_text['sugarword_index']
            
            # Hash Honey Passwords
            honeypassword_hasher_api_url = 'http://127.0.0.1:8002/honeypassword/hash_honeypasswords/'
            
            data = {"honeyword_list": honeyword_list}
            print(data)
            
            try:
                response = requests.post(honeypassword_hasher_api_url, json=data)  # Call API with honeywordlist as honeywords
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to send data to the honeypassword hasher API: {str(e)}")
            
            response_text = response.json()
            honeyhash_list = response_text['honeyword_hashes'] 
            print(response_text)
            salt = response_text['salt']
    
        except ValueError as e:
            raise Exception(f"Failed to parse JSON from the API response: {str(e)}")
        except KeyError as e:
            raise Exception(f"Missing expected key in the API response: {str(e)}")
        
        honey_passwords_entry = HoneyPasswords.objects.create(
            index=user,
            honeyPasswords=honeyhash_list,
            salt = salt
        )
        # Create a HoneyChecker entry
        # Send the sugarword_index and user information to the API
        honeychecker_api_url = 'http://127.0.0.1:8001/honeychecker/create_honeychecker_entry/'  # Adjust URL as needed
        
        data = {
            'user_index': user.random_index,
            'sugarword_index': sugarword_index
        }
        
        try:
            response = requests.post(honeychecker_api_url, json=data) # Call API
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send data to the honeychecker API: {str(e)}")
          
        
        # Generate DTE Seeds
        honeygenerate_seed_api_url = 'http://127.0.0.1:8002/honeydistributive/generate_seeds/'  # Adjust URL as needed
        
        try:
            response = requests.post(honeygenerate_seed_api_url) # Call API
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send data to the honeygenerator API: {str(e)}")
        
        response_text = response.json()
        ascii_seed = response_text['plaintext_seeds'] 
        
        # Encrypt DTE Seed
        honeyencrypt_seed_api_url = 'http://127.0.0.1:8002/honeydistributive/encrypt_dte_seeds/'  # Adjust URL as needed
        
        data = {
            'user_index': user.random_index,
            'sugarword_index': sugarword_index,
            'honey_hashes': honeyhash_list,
            'seed': ascii_seed
        }
        
        try:
            response = requests.post(honeyencrypt_seed_api_url, json=data) # Call API
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send data to the honeygenerator API: {str(e)}")
        
        response_text = response.json()
        ciphertext_b64 = response_text['ciphertext']
        params_dict = response_text['rbmrsa_parameters']

        encrypted_seed_entry = EncryptedSeed.objects.create(
            index= user,
            ciphertext=ciphertext_b64,
            rbmrsa_parameters=params_dict
        )
        
        return user

    def create_superuser(self, username, password="root", **kwargs):
        # create superuser from python shell if you want to create a custom superuser, otherwise, calling py manage.py create_superuser will 
        # always have password root. This is because django errors when i do create_superuser,
        # TypeError: CustomUserManager.create_superuser() missing 1 required positional argument: 'password'
        # But it only prompts for the username, then goes straight to the above error.
        # So I provided a default positional argument value so it works.
        
        # from login.models import CustomUser
        # CustomUser.objects.create_superuser(username='admin123', password='adminpassword123', email='admin@example.com')
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        
        if not username:
            raise ValueError('The Username field must be set')
        
        user = self.model(username=username, **kwargs)
        
        # Create User, Create HoneyPasswords Entry, Create HoneyPassword API Check Entry
        user.save(using=self._db)
        
        # Create a HoneyPasswords entry after the user is created
        honeypassword_generator_api_url = 'http://127.0.0.1:8002/honeypassword/generate_honeypasswords/'
        
        data = {
            'password': password
        }
        
        try:
            response = requests.get(honeypassword_generator_api_url, params=data)  # Call API with password as a query parameter
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send data to the honeypassword generator API: {str(e)}")
        
        try:
            # Parse the response as JSON
            response_text = response.json()  # Convert response text to a dictionary
            honeyword_list = response_text['honeyword_list'] 
            sugarword_index = response_text['sugarword_index']
            
            # Hash Honey Passwords
            honeypassword_hasher_api_url = 'http://127.0.0.1:8002/honeypassword/hash_honeypasswords/'
            
            data = {"honeyword_list": honeyword_list}
            
            try:
                response = requests.post(honeypassword_hasher_api_url, json=data)  # Call API with honeywordlist as honeywords
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to send data to the honeypassword hasher API: {str(e)}")
            
            response_text = response.json()
            honeyhash_list = response_text['honeyword_hashes'] 
            salt = response_text['salt']
    
        except ValueError as e:
            raise Exception(f"Failed to parse JSON from the API response: {str(e)}")
        except KeyError as e:
            raise Exception(f"Missing expected key in the API response: {str(e)}")
        
        honey_passwords_entry = HoneyPasswords.objects.create(
            index=user,
            honeyPasswords=honeyhash_list,
            salt = salt
        )
        
        # Create a HoneyChecker entry
        # Send the sugarword_index and user information to the API
        api_url = 'http://127.0.0.1:8001/honeychecker/create_honeychecker_entry/'  # Adjust URL as needed
        
        data = {
            'user_index': user.random_index,
            'sugarword_index': sugarword_index
        }
        
        try:
            response = requests.post(api_url, json=data) # Call API
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send data to the honeychecker API: {str(e)}")
        
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = "CustomUser"  # Singular name
        verbose_name_plural = "CustomUsers"  # Correct plural name
        
    username = models.CharField(_("Username"), max_length=50, unique=True)
    email = models.EmailField(_("Email"), unique=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    last_modified = models.DateTimeField(_("Last Modified"), auto_now=True)
    random_index = models.IntegerField(_("Random Index"),unique=True, null=True, blank=True)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'username'
    
    def get_random_index(self):
        return self.random_index

    def save(self, *args, **kwargs):
        if self.random_index is None:
            self.random_index = self.generate_unique_random_index()
        super().save(*args, **kwargs)

    def generate_unique_random_index(self):
        while True:
            index = random.randint(1, 9999)
            if not CustomUser.objects.filter(random_index=index).exists():
                return index
            
    def get_username(self):
        return self.username

    def __str__(self):
        return self.username
    
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True
    
    @property
    def is_admin_user(self):
        return self.is_staff
    
    # Overriding to avoid any reference to the password field
    def set_password(self, raw_password):
        pass

    def check_password(self, raw_password):
        return False  # Always return False or implement your own logic

    @property
    def password(self):
        return None  # Return None or customize the property logic
    
class HoneyPasswords(models.Model):
    class Meta:
        verbose_name = "Honey Password"  # Singular name
        verbose_name_plural = "Honey Passwords"  # Correct plural name
        
    index = models.OneToOneField(to=settings.AUTH_USER_MODEL, to_field= 'random_index', verbose_name=_("User"), on_delete=models.CASCADE, primary_key=True)
    honeyPasswords = models.JSONField(default=list)
    salt = models.CharField(_("Salt"), max_length=100, unique=False, blank= False, null= True)
    
    def __str__(self):
        try:
            query_object = UserGeneralInformation.objects.get(index=self.index) 
            return " ".join([query_object.first_name, query_object.middle_name, query_object.last_name])
        
        except UserGeneralInformation.DoesNotExist:
            return str(self.index) # Admin User Case
            
class UserGeneralInformation(models.Model):
    class Meta:
        verbose_name = "User Information"  # Singular name
        verbose_name_plural = "User Information"  # Correct plural name
        
    def __str__(self):
        return " ".join([self.first_name, self.middle_name, self.last_name])
    
    class CivilChoices(models.TextChoices):
        Single:tuple = 'Single','Single'
        Married:tuple = 'Married','Married'
        Widowed:tuple = 'Widowed','Widowed'
        Separated:tuple = 'Separated','Separated'
        
    class SexChoices(models.TextChoices):
        Male:tuple = 'Male','Male'
        Female:tuple = 'Female','Female'
        
    class RaceChoices(models.TextChoices):
        AMERICAN:tuple = 'American', 'American'
        ASIAN:tuple = 'Asian', 'Asian'
        BLACK:tuple = 'Black', 'Black or African American'
        WHITE:tuple = 'White', 'White'
        HISPANIC:tuple = 'Hispanic', 'Hispanic or Latino'
        NATIVE_AMERICAN:tuple = 'NativeAmerican', 'Native American'
        PACIFIC_ISLANDER:tuple = 'PacificIslander', 'Native Hawaiian or Pacific Islander'
        MULTIRACIAL:tuple = 'Multiracial', 'Two or More Races'
        OTHER:tuple = 'Other', 'Other'
        
    NationalityChoices = [(nat, nat) for nat in AllNationalities]
    ReligionChoices = [(rel, rel) for rel in AllReligion]
   
    index = models.OneToOneField(to=settings.AUTH_USER_MODEL, to_field='random_index', verbose_name=_("User"), on_delete=models.CASCADE)
    last_name = models.CharField(_("Last Name"), max_length=20, unique=False, blank= False, null= True)
    first_name = models.CharField(_("First Name"), max_length=20, unique=False, blank= False, null= True)
    middle_name = models.CharField(_("Middle Name"), max_length=20, unique=False, blank= False, null= True)
    suffix_name = models.CharField(_("Suffix Name"), max_length=20, unique=False, blank= True, null= True)
    civil_status = models.CharField(_("Marital Status"),max_length= 9, choices=CivilChoices.choices, null= True, blank= False)
    sex = models.CharField(_("Gender / Sex"), max_length=10, choices=SexChoices.choices, null= True, blank= False)
    nationality = models.CharField(_("Nationality"), max_length=33, choices=NationalityChoices, null= True, blank= False)
    religion = models.CharField(_("Religion"), max_length=28, choices=ReligionChoices, null= True, blank= False)
    philID = models.CharField(_("PhilID"), max_length=12, unique=False, blank= False, null= True)
    sss_number = models.CharField(_("SSS No."), max_length=9, unique=False, blank= False, null= True)
    passport_number = models.CharField(_("Passport No."), max_length=9, unique=False, blank= False, null= True)
    birth_date = models.DateField(_("Birth Date"), unique=False, blank= False, null= True)
    birth_place = models.CharField(_("Birth Place"), max_length=25, unique=False, blank= False, null= True)
    occupation = models.CharField(_("Occupation"), max_length=20, unique=False, blank= False, null= True)
    race = models.CharField(_("Race"),max_length= 20, choices=RaceChoices.choices, null= True, blank= False)
    isNonLocal = models.BooleanField(_("Non-Local?"), blank= False, null= True)
    isNoPersonalDataRelease = models.BooleanField(_("No personal data released to other parties?"), blank= False, null= True)
    isNoCompanyCommunication = models.BooleanField(_("No communication from company?"), blank= False, null= True)
    isConfidentialPatientRecord = models.BooleanField(_("Confidential Patient Record"), blank= False, null= True)
    
class UserMedicalInformation(models.Model):
    class Meta:
        verbose_name = "User Medical Information"  # Singular name
        verbose_name_plural = "User Medical Information"  # Correct plural name
        
    def __str__(self):
        query_object = UserGeneralInformation.objects.get(index=self.index)
        return " ".join([query_object.first_name, query_object.middle_name, query_object.last_name])
    
    class BloodTypeChoices(models.TextChoices):
        a_plus = "A+","A+"
        a_negative = "A-", "A-"
        b_plus = "B+", "B+"
        b_negative = "B-", "B-"
        ab_plus = "AB+", "AB+"
        ab_negative = "AB-", "AB-"
        o_plus = "O+", "O+"
        o_negative = "O-", "O-"
    
    index = models.OneToOneField(to=settings.AUTH_USER_MODEL, to_field='random_index', verbose_name=_("User"), on_delete=models.CASCADE)
    patient_number = models.CharField(_("Patient Number"), max_length=10, unique=False, blank= False, null= True)
    patient_identification = models.CharField(_("Patient ID"), max_length=10, unique=False, blank= False, null= True)
    patient_tin_number = models.CharField(_("Patient Tin No."), max_length=20, unique=False, blank= False, null= True)
    patient_phic_number = models.CharField(_("Patient Phic No."), max_length=10, unique=False, blank= False, null= True)
    mr_locator_no = models.CharField(_("M.R Locator No."), max_length=10, unique=False, null= True)
    blood_type = models.CharField(_("Blood Type"), max_length=5, choices=BloodTypeChoices, null= True, blank= False)
    weight = models.CharField(_("Weight"), max_length=5, unique=False, blank= False, null= True)
    temperature = models.CharField(_("Temperature"), max_length=5, unique=False, blank= False, null= True)
    blood_pressure = models.CharField(_("Blood Pressure"), max_length=5, unique=False, blank= False, null= True)
    GCS = models.CharField(_("GCS"), max_length=5, unique=False, blank= False, null= True)
    O2 = models.CharField(_("O2"), max_length=5, unique=False, blank= False, null= True)
    HR = models.CharField(_("HR"), max_length=5, unique=False, blank= False, null= True)
    RR = models.CharField(_("RR"), max_length=5, unique=False, blank= False, null= True)
    xray_file_number = models.CharField(_("Xray File No."), max_length=20, unique=False, blank= False, null= True)
    
class EncryptedSeed(models.Model):
    index = models.OneToOneField(to=settings.AUTH_USER_MODEL, to_field='random_index', verbose_name=_("User"), on_delete=models.CASCADE)
    ciphertext = models.TextField()
    rbmrsa_parameters = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EncryptedSeed {self.id} for user_index {self.user_index}"