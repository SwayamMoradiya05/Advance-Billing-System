import random
import time
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError


class Product(models.Model):
    """
    Product Model representing items, inventory goods, and taxable services
    managed in the Advance Billing System.
    """
    CATEGORY_CHOICES = [
        ('Electronics', 'Electronics & Hardware'),
        ('Office Supplies', 'Office Supplies & Stationery'),
        ('Groceries', 'Groceries & FMCG'),
        ('Apparel', 'Apparel & Clothing'),
        ('Industrial', 'Industrial & Electrical'),
        ('Services', 'Services & Maintenance'),
        ('General', 'General Goods'),
    ]

    GST_RATE_CHOICES = [
        (Decimal('0.00'), '0% (Exempt)'),
        (Decimal('5.00'), '5% (Essential Goods)'),
        (Decimal('12.00'), '12% (Standard Low)'),
        (Decimal('18.00'), '18% (Standard Rate)'),
        (Decimal('28.00'), '28% (Luxury / Premium)'),
    ]

    UNIT_CHOICES = [
        ('pcs', 'Pieces (pcs)'),
        ('box', 'Box (box)'),
        ('kg', 'Kilograms (kg)'),
        ('ltr', 'Liters (ltr)'),
        ('mtr', 'Meters (mtr)'),
        ('set', 'Set (set)'),
        ('pack', 'Pack (pack)'),
    ]

    sku = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Unique Product SKU code (e.g., PRD-1001)."
    )
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Full product title or item name."
    )
    category = models.CharField(
        max_length=100,
        default='General',
        choices=CATEGORY_CHOICES,
        help_text="Primary product classification category."
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Unit selling price before GST tax (in INR)."
    )
    stock = models.IntegerField(
        default=0,
        help_text="Current available inventory quantity in stock."
    )
    gst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('18.00'),
        choices=GST_RATE_CHOICES,
        help_text="Applicable Goods & Services Tax (GST) rate percentage."
    )
    hsn_code = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Harmonized System Nomenclature (HSN) code for GST invoicing."
    )
    unit = models.CharField(
        max_length=20,
        default='pcs',
        choices=UNIT_CHOICES,
        help_text="Unit of measurement (e.g., pcs, kg, box)."
    )
    min_stock_level = models.IntegerField(
        default=10,
        help_text="Minimum stock threshold to trigger low stock alerts."
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed product specifications, feature notes, or comments."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this product is active and available for billing."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.sku}) - ₹{self.price}"

    def clean(self):
        """Model level validation for price, stock, and tax fields."""
        super().clean()

        if self.price is not None and self.price < Decimal('0.00'):
            raise ValidationError({'price': 'Product price cannot be negative.'})

        if self.stock is not None and self.stock < 0:
            raise ValidationError({'stock': 'Inventory stock quantity cannot be negative.'})

        if self.gst_rate is not None and self.gst_rate < Decimal('0.00'):
            raise ValidationError({'gst_rate': 'GST rate percentage cannot be negative.'})

        if self.min_stock_level is not None and self.min_stock_level < 0:
            raise ValidationError({'min_stock_level': 'Minimum stock level threshold cannot be negative.'})

    def save(self, *args, **kwargs):
        """Auto-generate unique SKU if missing and run validation clean."""
        if not self.sku:
            self.sku = self.generate_unique_sku()

        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def generate_unique_sku(cls):
        """Generate a random unique SKU code e.g. PRD-1042."""
        for _ in range(100):
            candidate_sku = f"PRD-{random.randint(1000, 9999)}"
            if not cls.objects.filter(sku=candidate_sku).exists():
                return candidate_sku
        # Fallback timestamp-based unique SKU if collision occurs
        return f"PRD-{int(time.time()) % 100000}"

    @property
    def gst_amount(self):
        """Calculate GST tax amount per unit."""
        if self.price is None or self.gst_rate is None:
            return Decimal('0.00')
        amount = (self.price * self.gst_rate) / Decimal('100.00')
        return amount.quantize(Decimal('0.01'))

    @property
    def price_with_gst(self):
        """Calculate final selling price inclusive of GST tax."""
        if self.price is None:
            return Decimal('0.00')
        return (self.price + self.gst_amount).quantize(Decimal('0.01'))

    @property
    def total_stock_value(self):
        """Calculate total monetary value of current stock (excl. GST)."""
        if self.price is None or self.stock is None:
            return Decimal('0.00')
        return (self.price * Decimal(str(self.stock))).quantize(Decimal('0.01'))

    @property
    def total_stock_value_with_gst(self):
        """Calculate total monetary value of current stock inclusive of GST."""
        return (self.price_with_gst * Decimal(str(self.stock))).quantize(Decimal('0.01'))

    @property
    def is_low_stock(self):
        """Check if product stock level is at or below the reorder threshold."""
        return self.stock <= self.min_stock_level

    @property
    def stock_status(self):
        """Return human-readable stock status indicator."""
        if self.stock <= 0:
            return 'Out of Stock'
        elif self.is_low_stock:
            return 'Low Stock'
        return 'In Stock'
