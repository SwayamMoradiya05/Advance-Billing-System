from decimal import Decimal
import re
from customers.models import Customer


class CustomerSerializer:
    """
    Custom JSON serializer / deserializer helper for Customer objects,
    providing clean API request handling without external third-party dependencies.
    """

    @staticmethod
    def serialize(customer):
        """Serialize a Customer instance into a Python dictionary."""
        return {
            'id': customer.id,
            'customer_code': customer.customer_code,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'company_name': customer.company_name or '',
            'address': customer.address,
            'city': customer.city,
            'state': customer.state,
            'postal_code': customer.postal_code,
            'country': customer.country,
            'full_address': customer.full_address,
            'tax_id': customer.tax_id or '',
            'credit_limit': str(customer.credit_limit),
            'outstanding_balance': str(customer.outstanding_balance),
            'available_credit': str(customer.available_credit),
            'has_available_credit': customer.has_available_credit,
            'is_active': customer.is_active,
            'distributor_id': customer.distributor.id if customer.distributor else None,
            'notes': customer.notes,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
            'updated_at': customer.updated_at.isoformat() if customer.updated_at else None,
        }

    @staticmethod
    def validate_data(data, instance=None):
        """Validate input payload dictionary for creating or updating a customer."""
        errors = {}

        name = str(data.get('name', '')).strip()
        if not name or len(name) < 2:
            errors['name'] = "Customer name is required and must be at least 2 characters long."

        email = str(data.get('email', '')).strip().lower()
        if not email:
            errors['email'] = "Email address is required."
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors['email'] = "Enter a valid email address."
        else:
            query = Customer.objects.filter(email__iexact=email)
            if instance and instance.pk:
                query = query.exclude(pk=instance.pk)
            if query.exists():
                errors['email'] = "A customer with this email address already exists."

        phone = str(data.get('phone', '')).strip()
        if not phone:
            errors['phone'] = "Phone number is required."
        elif re.search(r'[a-zA-Z]', phone):
            errors['phone'] = "Phone number cannot contain alphabetic characters."
        else:
            digits = re.sub(r'\D', '', phone)
            if len(digits) < 7 or len(digits) > 15:
                errors['phone'] = "Phone number must contain between 7 and 15 digits."

        address = str(data.get('address', '')).strip()
        if not address:
            errors['address'] = "Address is required."

        if 'credit_limit' in data and data['credit_limit'] is not None:
            try:
                credit_limit = Decimal(str(data['credit_limit']))
                if credit_limit < Decimal('0.00'):
                    errors['credit_limit'] = "Credit limit cannot be negative."
            except Exception:
                errors['credit_limit'] = "Invalid decimal number for credit limit."

        if 'outstanding_balance' in data and data['outstanding_balance'] is not None:
            try:
                balance = Decimal(str(data['outstanding_balance']))
                if balance < Decimal('0.00'):
                    errors['outstanding_balance'] = "Outstanding balance cannot be negative."
            except Exception:
                errors['outstanding_balance'] = "Invalid decimal number for outstanding balance."

        return errors
