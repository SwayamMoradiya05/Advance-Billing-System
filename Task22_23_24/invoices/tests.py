from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.contrib.auth import get_user_model

from customers.models import Customer
from products.models import Product
from accounts.models import DistributorProfile
from invoices.models import Invoice, InvoiceItem
from invoices.forms import InvoiceForm, InvoiceItemForm, InvoiceItemFormSet
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


class InvoiceFormAndAccessTestCase(TestCase):
    """
    Test suite for Invoice Form validation, dynamic dropdown choices, stock checks,
    and Admin/Distributor role-based access control.
    """

    def setUp(self):
        self.client = Client()
        
        # 1. System Admin User
        self.admin_user = User.objects.create_superuser(username="admin_user", email="admin@test.com", password="password123")
        
        # 2. Distributor User
        self.distributor_user = User.objects.create_user(username="dist_user", email="dist@test.com", password="password123")
        self.distributor_profile = DistributorProfile.objects.create(
            user=self.distributor_user,
            phone="1234567890",
            distributor_id="DIST-9999"
        )
        
        # 3. Regular Customer / Non-operator User
        self.customer_user = User.objects.create_user(username="cust_user", email="cust@test.com", password="password123")

        # Sample Customers
        self.customer1 = Customer.objects.create(name="Customer One", email="c1@test.com", phone="1111111111", address="Addr 1", distributor=self.distributor_user)
        self.customer2 = Customer.objects.create(name="Customer Two", email="c2@test.com", phone="2222222222", address="Addr 2")

        # Sample Products
        self.product_in_stock = Product.objects.create(name="Laptop Pro", price=Decimal("50000.00"), stock=10, gst_rate=Decimal("18.00"))
        self.product_low_stock = Product.objects.create(name="Mouse Wireless", price=Decimal("800.00"), stock=2, gst_rate=Decimal("18.00"))

    def test_invoice_creation_access_control(self):
        """Test invoice creation view permissions: Allowed for Admin and Distributor, Denied for Customer."""
        url = reverse('invoice_create')

        # Unauthenticated -> Redirect to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Customer User -> Denied (Redirected to dashboard with error)
        self.client.login(username="cust_user", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Distributor User -> Allowed
        self.client.login(username="dist_user", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Admin User -> Allowed
        self.client.login(username="admin_user", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_stock_validation_in_form(self):
        """Test line item form clean method blocks quantity exceeding available inventory stock."""
        form_data = {
            'product': self.product_low_stock.id,
            'quantity': 10,  # Available stock is only 2
            'unit_price': '800.00',
            'gst_rate': '18.00',
            'discount_percentage': '0.00',
        }
        form = InvoiceItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)
        self.assertIn('Insufficient stock', form.errors['quantity'][0])

    def test_valid_invoice_creation_formset_submission(self):
        """Test successful submission of InvoiceForm + InvoiceItemFormSet by Distributor."""
        self.client.login(username="dist_user", password="password123")
        url = reverse('invoice_create')

        form_data = {
            'customer': self.customer1.id,
            'invoice_date': timezone.now().date().strftime('%Y-%m-%d'),
            'status': 'PENDING',
            'payment_method': 'BANK_TRANSFER',
            'payment_terms': 'Net 30',
            'discount_amount': '100.00',
            'amount_paid': '0.00',
            'notes': 'Test invoice submission',
            'terms_and_conditions': 'Standard terms',
            
            # Management Form
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            
            # Item Row 0
            'items-0-product': self.product_in_stock.id,
            'items-0-quantity': '2',
            'items-0-unit_price': '50000.00',
            'items-0-gst_rate': '18.00',
            'items-0-discount_percentage': '0.00',
            'items-0-description': 'High performance laptop',
        }

        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 302)  # Successful creation redirects to detail view

        created_invoice = Invoice.objects.filter(customer=self.customer1).first()
        self.assertIsNotNone(created_invoice)
        self.assertEqual(created_invoice.items.count(), 1)
        self.assertEqual(created_invoice.subtotal, Decimal("100000.00"))
        self.assertEqual(created_invoice.tax_amount, Decimal("18000.00"))
        # Grand total = (100000 + 18000) - 100 = 117900.00
        self.assertEqual(created_invoice.grand_total, Decimal("117900.00"))

    def test_api_customer_and_product_details(self):
        """Test API endpoints for dynamic customer and product lookup."""
        self.client.login(username="admin_user", password="password123")
        
        # Customer Detail API
        cust_url = reverse('api_invoice_customer_detail', kwargs={'pk': self.customer1.id})
        res_cust = self.client.get(cust_url)
        self.assertEqual(res_cust.status_code, 200)
        self.assertTrue(res_cust.json()['success'])
        self.assertEqual(res_cust.json()['customer']['name'], self.customer1.name)

        # Product Detail API
        prod_url = reverse('api_invoice_product_detail', kwargs={'pk': self.product_in_stock.id})
        res_prod = self.client.get(prod_url)
        self.assertEqual(res_prod.status_code, 200)
        self.assertTrue(res_prod.json()['success'])
        self.assertEqual(res_prod.json()['product']['sku'], self.product_in_stock.sku)

    def test_invoice_pdf_download_view(self):
        """Test PDF generation view returns 200 OK and valid PDF binary bytes."""
        invoice = Invoice.objects.create(customer=self.customer1, created_by=self.admin_user)
        InvoiceItem.objects.create(invoice=invoice, product=self.product_in_stock, quantity=2)

        # Unauthenticated -> redirect to login
        pdf_url = reverse('invoice_pdf', kwargs={'pk': invoice.id})
        response = self.client.get(pdf_url)
        self.assertEqual(response.status_code, 302)

        # Authenticated -> 200 OK with PDF binary stream
        self.client.login(username="admin_user", password="password123")
        response = self.client.get(pdf_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('qr_base64', response.context)
        self.assertTrue(response.context['qr_base64'].startswith('data:image/png;base64,'))
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(f'filename="Invoice_{invoice.invoice_number}.pdf"', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))
