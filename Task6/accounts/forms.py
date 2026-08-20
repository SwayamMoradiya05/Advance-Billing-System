import re
from django import forms
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )
    remember_me = forms.BooleanField(required=False, initial=False)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                try:
                    user_obj = User.objects.get(username=username)
                    if user_obj.check_password(password) and not user_obj.is_active:
                        raise forms.ValidationError('This user account is inactive.')
                except User.DoesNotExist:
                    pass
                raise forms.ValidationError('Invalid username or password.')

            cleaned_data['user'] = user

        return cleaned_data

class DistributorLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Distributor Email or ID',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )
    remember_me = forms.BooleanField(required=False, initial=False)

    def clean(self):
        cleaned_data = super().clean()
        username_input = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username_input and password:
            clean_identifier = username_input.strip()

            # 1. Authenticate directly by username
            user = authenticate(username=clean_identifier, password=password)

            # 2. Authenticate by Email
            if user is None:
                users_by_email = User.objects.filter(email__iexact=clean_identifier)
                for u in users_by_email:
                    authenticated_user = authenticate(username=u.username, password=password)
                    if authenticated_user:
                        user = authenticated_user
                        break

            # 3. Authenticate by Distributor ID (e.g. DIST-8842)
            if user is None:
                from .models import DistributorProfile
                profiles = DistributorProfile.objects.filter(distributor_id__iexact=clean_identifier)
                for p in profiles:
                    authenticated_user = authenticate(username=p.user.username, password=password)
                    if authenticated_user:
                        user = authenticated_user
                        break

            if user is None:
                raise forms.ValidationError('Invalid distributor credentials.')

            cleaned_data['user'] = user

        return cleaned_data

class DistributorRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. David Miller',
            'autofocus': True,
        }),
        label="Full Name"
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. david@apexlogistics.com',
        }),
        label="Email Address"
    )

    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. +1 555-019-8842',
        }),
        label="Phone Number"
    )

    company_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Apex Global Supplies (Optional)',
        }),
        label="Company Name"
    )

    password = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
        }),
        label="Create Password"
    )

    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
        }),
        label="Confirm Password"
    )

    agree_terms = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must accept the Terms of Service to register.'}
    )

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if len(full_name) < 2:
            raise forms.ValidationError('Full name must be at least 2 characters long.')
        if re.search(r'\d', full_name):
            raise forms.ValidationError('Full name should not contain numeric digits.')
        return full_name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise forms.ValidationError('Please enter a valid email address format.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address is already registered.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if re.search(r'[a-zA-Z]', phone):
            raise forms.ValidationError('Phone number cannot contain alphabetic characters. It must contain numerical digits only.')
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7 or len(digits) > 15:
            raise forms.ValidationError('Please enter a valid 7 to 15 digit numerical phone number.')
        return phone

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
            if not (re.search(r'[A-Za-z]', password) and re.search(r'[0-9]', password)):
                raise forms.ValidationError('Password must contain a mix of letters and numbers.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match. Please re-enter.')

        return cleaned_data


class DistributorProfileForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-dark text-light border-secondary',
            'placeholder': 'Full Name',
        }),
        label="Full Name"
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-dark text-light border-secondary',
            'placeholder': 'Email Address',
        }),
        label="Email Address"
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-dark text-light border-secondary',
            'placeholder': 'Phone Number',
        }),
        label="Phone Number"
    )
    company_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-dark text-light border-secondary',
            'placeholder': 'Company / Business Name',
        }),
        label="Company Name"
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if len(full_name) < 2:
            raise forms.ValidationError('Full name must be at least 2 characters long.')
        if re.search(r'\d', full_name):
            raise forms.ValidationError('Full name should not contain numeric digits.')
        return full_name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise forms.ValidationError('Please enter a valid email address format.')
        existing_users = User.objects.filter(email__iexact=email)
        if self.user:
            existing_users = existing_users.exclude(pk=self.user.pk)
        if existing_users.exists():
            raise forms.ValidationError('An account with this email address is already registered.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if re.search(r'[a-zA-Z]', phone):
            raise forms.ValidationError('Phone number cannot contain alphabetic characters.')
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7 or len(digits) > 15:
            raise forms.ValidationError('Please enter a valid 7 to 15 digit numerical phone number.')
        return phone

