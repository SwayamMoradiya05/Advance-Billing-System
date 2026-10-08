import re
from decimal import Decimal
from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):
    """
    Form for creating and updating Customer records with styled form widgets
    and field validation.
    """
    class Meta:
        model = Customer
        fields = [
            'name',
            'email',
            'phone',
            'company_name',
            'address',
            'city',
            'state',
            'postal_code',
            'country',
            'tax_id',
            'credit_limit',
            'outstanding_balance',
            'is_active',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name or Contact Person',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'customer@example.com',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 555-019-2834',
                'required': True,
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business or Enterprise Name (Optional)',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Street Address, Suite / Floor',
                'required': True,
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State / Province',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ZIP / Postal Code',
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country',
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GSTIN or Tax Registration ID (Optional)',
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '10000.00',
            }),
            'outstanding_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Internal notes or preferences...',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("Customer name must be at least 2 characters long.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        # Verify unique email excluding current instance
        query = Customer.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError("A customer with this email address already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if re.search(r'[a-zA-Z]', phone):
            raise forms.ValidationError("Phone number cannot contain alphabetic characters.")
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7 or len(digits) > 15:
            raise forms.ValidationError("Please provide a valid 7 to 15 digit numerical phone number.")
        return phone

    def clean_credit_limit(self):
        credit_limit = self.cleaned_data.get('credit_limit')
        if credit_limit is not None and credit_limit < Decimal('0.00'):
            raise forms.ValidationError("Credit limit cannot be negative.")
        return credit_limit

    def clean_outstanding_balance(self):
        balance = self.cleaned_data.get('outstanding_balance')
        if balance is not None and balance < Decimal('0.00'):
            raise forms.ValidationError("Outstanding balance cannot be negative.")
        return balance


class CustomerFilterForm(forms.Form):
    """
    Search, filter, and sort form for customer directory list.
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Search by name, company, email, phone, city, or code...',
            'id': 'searchInput',
            'autocomplete': 'off',
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Statuses'),
            ('active', 'Active Only'),
            ('inactive', 'Inactive Only'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'statusSelect',
        })
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('name', 'Name (A-Z)'),
            ('-name', 'Name (Z-A)'),
            ('-outstanding_balance', 'Highest Outstanding Balance'),
            ('-credit_limit', 'Highest Credit Limit'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'sortSelect',
        })
    )

