import re
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class DistributorRegistrationForm(forms.Form):
    """
    Django Form for Distributor Registration.
    Captures Name, Email, Phone, Company, Password, and Confirm Password with
    human-crafted field-level validation logic.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-dark',
            'placeholder': 'e.g. David Miller',
            'autofocus': True,
        }),
        label="Full Name"
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-dark',
            'placeholder': 'e.g. david@apexlogistics.com',
        }),
        label="Email Address"
    )

    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-dark',
            'placeholder': 'e.g. +1 555-019-8842',
        }),
        label="Phone Number"
    )

    company_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-dark',
            'placeholder': 'e.g. Apex Global Supplies (Optional)',
        }),
        label="Company / Business Name"
    )

    password = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-dark',
            'placeholder': '••••••••',
        }),
        label="Create Password"
    )

    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-dark',
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
            raise ValidationError('Full name must be at least 2 characters long.')
        if re.search(r'\d', full_name):
            raise ValidationError('Full name should not contain numeric digits.')
        return full_name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError('Please enter a valid email address format.')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address is already registered.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if re.search(r'[a-zA-Z]', phone):
            raise ValidationError('Phone number cannot contain alphabetic characters. It must contain numerical digits only.')
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7 or len(digits) > 15:
            raise ValidationError('Please enter a valid 7 to 15 digit numerical phone number.')
        return phone

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
            if not (re.search(r'[A-Za-z]', password) and re.search(r'[0-9]', password)):
                raise ValidationError('Password must contain a mix of letters and numbers.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match. Please re-enter.')

        return cleaned_data
