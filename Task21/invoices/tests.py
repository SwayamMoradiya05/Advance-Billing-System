from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.contrib.auth import get_user_model

from customers.models import Customer
from products.models import Product
from invoices.models import Invoice, InvoiceItem
from invoices.serializers import InvoiceSerializer, InvoiceItemSerializer

User = get_user_model()


class InvoiceModelTestCase(TestCase):
    """
    Test suite for Invoice and InvoiceItem models, calculations, foreign key integrity,
    and validation constraints.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="distributor_user", password="password123")
        self.customer = Customer.objects.create(
            name="Acme Logistics",
            email="contact@acme.com",
            phone="9876543210",
            address="123 Industrial Area",
            distributor=self.user
        )
        self.product1 = Product.objects.create(
            name="Industrial Battery 12V",
            category="Industrial",
            price=Decimal("1000.00"),
            stock=50,
            gst_rate=Decimal("18.00")
        )
        self.product2 = Product.objects.create(
            name="Copper Wire 100m",
            category="Industrial",
            price=Decimal("500.00"),
            stock=100,
            gst_rate=Decimal("12.00")
        )

    def test_invoice_auto_number_and_creation(self):
        """Test auto-generation of unique invoice_number and default fields."""
        invoice = Invoice.objects.create(
            customer=self.customer,
            created_by=self.user
        )
        self.assertTrue(invoice.invoice_number.startswith("INV-"))
        self.assertEqual(invoice.status, "DRAFT")
        self.assertEqual(invoice.grand_total, Decimal("0.00"))
        self.assertEqual(invoice.customer, self.customer)
        self.assertEqual(invoice.created_by, self.user)

    def test_invoice_item_creation_and_auto_pricing(self):
        """Test InvoiceItem auto-fills price and GST rate from Product and updates parent Invoice."""
        invoice = Invoice.objects.create(customer=self.customer)
        item = InvoiceItem.objects.create(
            invoice=invoice,
            product=self.product1,
            quantity=2
        )
        # Check snapshot from product
        self.assertEqual(item.unit_price, Decimal("1000.00"))
        self.assertEqual(item.gst_rate, Decimal("18.00"))
        
        # Line subtotal = 1000 * 2 = 2000.00
        self.assertEqual(item.line_subtotal, Decimal("2000.00"))
        # GST tax = 2000 * 18% = 360.00
        self.assertEqual(item.tax_amount, Decimal("360.00"))
        # Total line = 2000 + 360 = 2360.00
        self.assertEqual(item.total_amount, Decimal("2360.00"))

        # Parent invoice totals refreshed automatically
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, Decimal("2000.00"))
        self.assertEqual(invoice.tax_amount, Decimal("360.00"))
        self.assertEqual(invoice.grand_total, Decimal("2360.00"))
        self.assertEqual(invoice.balance_due, Decimal("2360.00"))

    def test_multiple_invoice_items_total_calculation(self):
        """Test multiple invoice items update subtotal, GST tax, and grand total correctly."""
        invoice = Invoice.objects.create(customer=self.customer, discount_amount=Decimal("100.00"))
        
        # Item 1: 2x 1000 @ 18% GST -> Subtotal 2000, Tax 360
        InvoiceItem.objects.create(invoice=invoice, product=self.product1, quantity=2)
        
        # Item 2: 3x 500 @ 12% GST -> Subtotal 1500, Tax 180
        InvoiceItem.objects.create(invoice=invoice, product=self.product2, quantity=3)

        invoice.refresh_from_db()
        # Subtotal: 2000 + 1500 = 3500.00
        self.assertEqual(invoice.subtotal, Decimal("3500.00"))
        # Tax: 360 + 180 = 540.00
        self.assertEqual(invoice.tax_amount, Decimal("540.00"))
        # Grand total: (3500 + 540) - 100 = 3940.00
        self.assertEqual(invoice.grand_total, Decimal("3940.00"))
        self.assertEqual(invoice.total_items_count, 2)

    def test_item_deletion_updates_invoice_totals(self):
        """Test deleting an invoice item recalculates the parent invoice totals."""
        invoice = Invoice.objects.create(customer=self.customer)
        item1 = InvoiceItem.objects.create(invoice=invoice, product=self.product1, quantity=1)
        item2 = InvoiceItem.objects.create(invoice=invoice, product=self.product2, quantity=1)

        invoice.refresh_from_db()
        self.assertEqual(invoice.total_items_count, 2)

        item1.delete()
        invoice.refresh_from_db()
        self.assertEqual(invoice.total_items_count, 1)
        self.assertEqual(invoice.subtotal, Decimal("500.00"))

    def test_foreign_key_protect_on_customer_deletion(self):
        """Test that deleting a customer with invoices raises ProtectedError."""
        invoice = Invoice.objects.create(customer=self.customer)
        with self.assertRaises(ProtectedError):
            self.customer.delete()

    def test_foreign_key_protect_on_product_deletion(self):
        """Test that deleting a product referenced in an InvoiceItem raises ProtectedError."""
        invoice = Invoice.objects.create(customer=self.customer)
        InvoiceItem.objects.create(invoice=invoice, product=self.product1, quantity=1)
        
        with self.assertRaises(ProtectedError):
            self.product1.delete()

    def test_invoice_deletion_cascades_to_items(self):
        """Test deleting an invoice cascades and deletes associated invoice items."""
        invoice = Invoice.objects.create(customer=self.customer)
        item = InvoiceItem.objects.create(invoice=invoice, product=self.product1, quantity=1)
        item_id = item.id

        invoice.delete()
        self.assertFalse(InvoiceItem.objects.filter(id=item_id).exists())

    def test_due_date_validation(self):
        """Test validation error when due_date is before invoice_date."""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        invoice = Invoice(
            customer=self.customer,
            invoice_date=today,
            due_date=yesterday
        )
        with self.assertRaises(ValidationError):
            invoice.clean()

    def test_overdue_property(self):
        """Test is_overdue property logic."""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        ten_days_ago = today - timedelta(days=10)
        invoice = Invoice.objects.create(
            customer=self.customer,
            invoice_date=ten_days_ago,
            due_date=yesterday,
            status='PENDING',
            grand_total=Decimal('100.00'),
            amount_paid=Decimal('0.00')
        )
        self.assertTrue(invoice.is_overdue)

        # Mark as paid -> should no longer be overdue
        invoice.amount_paid = Decimal('100.00')
        invoice.status = 'PAID'
        invoice.save()
        self.assertFalse(invoice.is_overdue)

    def test_serializers(self):
        """Test InvoiceSerializer and InvoiceItemSerializer data output."""
        invoice = Invoice.objects.create(customer=self.customer)
        item = InvoiceItem.objects.create(invoice=invoice, product=self.product1, quantity=2)
        
        invoice.refresh_from_db()
        serialized = InvoiceSerializer.serialize(invoice)
        self.assertEqual(serialized['invoice_number'], invoice.invoice_number)
        self.assertEqual(serialized['customer_name'], self.customer.name)
        self.assertEqual(len(serialized['items']), 1)
        self.assertEqual(serialized['items'][0]['product_name'], self.product1.name)
