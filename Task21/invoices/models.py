import random
import time
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Invoice(models.Model):
    """
    Invoice Model representing commercial sales transactions, customer billing,
    tax summaries, and payment tracking within the Advance Billing System.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('CANCELLED', 'Cancelled'),
        ('OVERDUE', 'Overdue'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('UPI', 'UPI Payment'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CHEQUE', 'Cheque'),
        ('CREDIT', 'Store Credit / Account'),
    ]

    invoice_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Unique identifier for the invoice e.g., INV-20260824-1001"
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="Customer or billing account linked to this invoice."
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_invoices',
        help_text="User or distributor who generated this invoice."
    )
    invoice_date = models.DateField(
        default=timezone.now,
        help_text="Date on which the invoice was issued."
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Payment due date for this invoice."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True,
        help_text="Current settlement and billing status of the invoice."
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default='CASH',
        blank=True,
        help_text="Mode of payment agreed or received."
    )
    payment_terms = models.CharField(
        max_length=50,
        blank=True,
        default="Net 30",
        help_text="Standard terms of payment (e.g. Due on Receipt, Net 15, Net 30)."
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Sum of line item totals before taxes and overall discount."
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total calculated Goods & Services Tax (GST) across all items."
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Overall invoice-level discount applied to total bill."
    )
    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Final payable invoice amount inclusive of GST and discounts."
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total payments collected against this invoice."
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes or customer-visible memo."
    )
    terms_and_conditions = models.TextField(
        blank=True,
        default="Thank you for your business! Payment is due according to agreed terms.",
        help_text="Standard legal terms, refund policies, or payment instructions."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ['-created_at']

    def __str__(self):
        customer_name = self.customer.name if self.customer else "Unknown Customer"
        return f"Invoice {self.invoice_number} - {customer_name} (₹{self.grand_total})"

    def clean(self):
        """Model validation logic for date consistency and non-negative financial values."""
        super().clean()

        if self.invoice_date and self.due_date and self.due_date < self.invoice_date:
            raise ValidationError({'due_date': 'Due date cannot be earlier than the issue date.'})

        if self.subtotal < Decimal('0.00'):
            raise ValidationError({'subtotal': 'Subtotal amount cannot be negative.'})

        if self.tax_amount < Decimal('0.00'):
            raise ValidationError({'tax_amount': 'Tax amount cannot be negative.'})

        if self.discount_amount < Decimal('0.00'):
            raise ValidationError({'discount_amount': 'Discount amount cannot be negative.'})

        if self.grand_total < Decimal('0.00'):
            raise ValidationError({'grand_total': 'Grand total amount cannot be negative.'})

        if self.amount_paid < Decimal('0.00'):
            raise ValidationError({'amount_paid': 'Amount paid cannot be negative.'})

    def save(self, *args, **kwargs):
        """Auto-generate invoice number if missing and run full validation."""
        if not self.invoice_number:
            self.invoice_number = self.generate_unique_invoice_number()

        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def generate_unique_invoice_number(cls):
        """Generate a structured unique invoice code e.g. INV-20260824-4821."""
        date_str = timezone.now().strftime('%Y%m%d')
        for _ in range(100):
            candidate = f"INV-{date_str}-{random.randint(1000, 9999)}"
            if not cls.objects.filter(invoice_number=candidate).exists():
                return candidate
        # Fallback timestamp code
        return f"INV-{date_str}-{int(time.time()) % 10000}"

    @property
    def balance_due(self):
        """Calculate remaining unsettled balance on this invoice."""
        balance = self.grand_total - self.amount_paid
        return max(Decimal('0.00'), balance).quantize(Decimal('0.01'))

    @property
    def is_overdue(self):
        """Return True if due_date is past and unpaid balance remains."""
        if not self.due_date:
            return False
        today = timezone.now().date()
        return self.due_date < today and self.balance_due > Decimal('0.00') and self.status not in ['PAID', 'CANCELLED']

    @property
    def total_items_count(self):
        """Return total count of individual line items in this invoice."""
        return self.items.count()

    def calculate_totals(self, save_instance=True):
        """
        Recalculate subtotal, tax amount, and grand total from line items.
        """
        items = self.items.all()
        calculated_subtotal = Decimal('0.00')
        calculated_tax = Decimal('0.00')

        for item in items:
            calculated_subtotal += item.line_subtotal
            calculated_tax += item.tax_amount

        self.subtotal = calculated_subtotal.quantize(Decimal('0.01'))
        self.tax_amount = calculated_tax.quantize(Decimal('0.01'))
        
        net_total = (self.subtotal + self.tax_amount) - self.discount_amount
        self.grand_total = max(Decimal('0.00'), net_total).quantize(Decimal('0.01'))

        # Auto-update status if paid in full
        if self.amount_paid >= self.grand_total and self.grand_total > Decimal('0.00') and self.status != 'CANCELLED':
            self.status = 'PAID'
        elif self.amount_paid > Decimal('0.00') and self.amount_paid < self.grand_total and self.status not in ['CANCELLED', 'DRAFT']:
            self.status = 'PARTIALLY_PAID'

        if save_instance:
            super().save(update_fields=['subtotal', 'tax_amount', 'grand_total', 'status'])


class InvoiceItem(models.Model):
    """
    InvoiceItem Model representing individual product line items attached to an Invoice.
    Snapshots product pricing and GST rate to preserve historical integrity.
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Parent invoice associated with this line item."
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='invoice_items',
        help_text="Product or inventory item billed in this line."
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Quantity of product purchased."
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Unit selling price at time of billing (excl. GST). Defaults to Product price if left blank."
    )
    gst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Applicable Goods & Services Tax (GST) rate percentage. Defaults to Product GST rate if left blank."
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Line item discount percentage (0 to 100%)."
    )
    line_subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Line subtotal before GST (unit_price * quantity)."
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Calculated GST tax amount for this line item."
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Calculated net total amount for this line item (subtotal + tax - discount)."
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Optional custom description or serial numbers for this line item."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Invoice Item"
        verbose_name_plural = "Invoice Items"
        ordering = ['id']

    def __str__(self):
        product_name = self.product.name if self.product else "Unknown Product"
        inv_num = self.invoice.invoice_number if self.invoice else "N/A"
        return f"{self.quantity}x {product_name} @ ₹{self.unit_price} ({inv_num})"

    def clean(self):
        """Validate non-zero quantity and valid percentage/pricing fields."""
        super().clean()

        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than zero.'})

        if self.unit_price is not None and self.unit_price < Decimal('0.00'):
            raise ValidationError({'unit_price': 'Unit price cannot be negative.'})

        if self.gst_rate is not None and self.gst_rate < Decimal('0.00'):
            raise ValidationError({'gst_rate': 'GST rate cannot be negative.'})

        if self.discount_percentage is not None:
            if self.discount_percentage < Decimal('0.00') or self.discount_percentage > Decimal('100.00'):
                raise ValidationError({'discount_percentage': 'Discount percentage must be between 0% and 100%.'})

    def calculate_amounts(self):
        """
        Populate unit price and GST rate from Product if missing, and compute
        line_subtotal, tax_amount, and total_amount.
        """
        if self.product:
            if self.unit_price is None:
                self.unit_price = self.product.price
            if self.gst_rate is None:
                self.gst_rate = self.product.gst_rate

        if self.unit_price is None:
            self.unit_price = Decimal('0.00')
        if self.gst_rate is None:
            self.gst_rate = Decimal('0.00')
        if self.quantity is None:
            self.quantity = 1
        if self.discount_percentage is None:
            self.discount_percentage = Decimal('0.00')

        qty_decimal = Decimal(str(self.quantity))
        base_subtotal = (self.unit_price * qty_decimal).quantize(Decimal('0.01'))
        
        discount_fraction = self.discount_percentage / Decimal('100.00')
        discount_val = (base_subtotal * discount_fraction).quantize(Decimal('0.01'))
        
        taxable_amount = base_subtotal - discount_val
        
        gst_fraction = self.gst_rate / Decimal('100.00')
        line_tax = (taxable_amount * gst_fraction).quantize(Decimal('0.01'))

        self.line_subtotal = base_subtotal
        self.tax_amount = line_tax
        self.total_amount = (taxable_amount + line_tax).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        """Auto-calculate amounts, run clean validation, and trigger parent invoice total recalculation."""
        self.calculate_amounts()
        self.full_clean()
        super().save(*args, **kwargs)
        
        if self.invoice:
            self.invoice.calculate_totals(save_instance=True)

    def delete(self, *args, **kwargs):
        """Ensure parent invoice totals are updated after item deletion."""
        parent_invoice = self.invoice
        super().delete(*args, **kwargs)
        if parent_invoice:
            parent_invoice.calculate_totals(save_instance=True)
