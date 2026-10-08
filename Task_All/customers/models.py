import re
import random
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class Customer(models.Model):
    """
    Customer Model representing clients, retail buyers, or commercial accounts
    registered within the Advance Billing System.
    """
    customer_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique Identifier for Customer e.g., CUST-4821"
    )
    name = models.CharField(
        max_length=255,
        help_text="Full contact name or primary representative name."
    )
    email = models.EmailField(
        max_length=255,
        db_index=True,
        help_text="Primary notification & invoicing email address."
    )
    phone = models.CharField(
        max_length=20,
        help_text="Primary telephone or mobile number."
    )
    company_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Registered company or business entity name (optional)."
    )
    address = models.TextField(
        help_text="Street address, building number, or billing location."
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="City or town."
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="State, province, or region."
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="ZIP or postal code."
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default="India",
        help_text="Country location."
    )
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Tax Registration ID or GSTIN number (optional)."
    )
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("10000.00"),
        help_text="Maximum allowed credit for deferred billing transactions."
    )
    outstanding_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Current unsettled balance."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this customer account is active."
    )
    distributor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_customers",
        help_text="Distributor account managing this customer."
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes or special instructions."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['-created_at']

    def __str__(self):
        if self.company_name:
            return f"{self.name} - {self.company_name} ({self.customer_code})"
        return f"{self.name} ({self.customer_code})"

    def clean(self):
        """Model validation rules for clean customer attributes."""
        super().clean()
        
        # Phone validation: no alphabetic characters allowed
        if self.phone and re.search(r'[a-zA-Z]', self.phone):
            raise ValidationError({'phone': 'Phone number cannot contain alphabetic characters.'})
        
        # Numeric digits check for phone
        if self.phone:
            digits = re.sub(r'\D', '', self.phone)
            if len(digits) < 7 or len(digits) > 15:
                raise ValidationError({'phone': 'Phone number must contain between 7 and 15 digits.'})

        # Negative check for financial fields
        if self.credit_limit < Decimal('0.00'):
            raise ValidationError({'credit_limit': 'Credit limit cannot be negative.'})

        if self.outstanding_balance < Decimal('0.00'):
            raise ValidationError({'outstanding_balance': 'Outstanding balance cannot be negative.'})

    def save(self, *args, **kwargs):
        """Auto-generate unique customer code if missing and execute full validation."""
        if not self.customer_code:
            self.customer_code = self.generate_unique_code()
        
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def generate_unique_code(cls):
        """Generate a random unique customer code e.g. CUST-8492."""
        for _ in range(100):
            code = f"CUST-{random.randint(1000, 9999)}"
            if not cls.objects.filter(customer_code=code).exists():
                return code
        # Fallback timestamp-based code if collision occurs
        import time
        return f"CUST-{int(time.time()) % 100000}"

    @property
    def available_credit(self):
        """Calculate remaining available credit limit."""
        return max(Decimal("0.00"), self.credit_limit - self.outstanding_balance)

    @property
    def has_available_credit(self):
        """Return True if customer can take on additional credit."""
        return self.available_credit > Decimal("0.00")

    @property
    def full_address(self):
        """Combine address components into a single formatted string."""
        parts = [p for p in [self.address, self.city, self.state, self.postal_code, self.country] if p]
        return ", ".join(parts)
