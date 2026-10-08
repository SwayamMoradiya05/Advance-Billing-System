import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Product
from .forms import ProductForm, ProductSearchFilterForm
from .serializers import ProductSerializer


class ProductModelTestCase(TestCase):
    """
    Unit tests for the Product model schema, validations, and calculated properties.
    """

    def setUp(self):
        self.product = Product.objects.create(
            name="Wireless Optical Mouse",
            category="Electronics",
            price=Decimal("500.00"),
            stock=25,
            gst_rate=Decimal("18.00"),
            hsn_code="84716060",
            unit="pcs",
            min_stock_level=10,
            description="Ergonomic 2.4GHz wireless mouse."
        )

    def test_product_creation_and_auto_sku(self):
        """Test that product is created with auto-generated SKU if left blank."""
        self.assertTrue(self.product.sku.startswith("PRD-"))
        self.assertEqual(str(self.product), f"Wireless Optical Mouse ({self.product.sku}) - ₹500.00")

    def test_computed_gst_and_price(self):
        """Test GST tax amount and price inclusive of GST computation."""
        # price = 500.00, gst_rate = 18.00% => gst_amount = 90.00, price_with_gst = 590.00
        self.assertEqual(self.product.gst_amount, Decimal("90.00"))
        self.assertEqual(self.product.price_with_gst, Decimal("590.00"))

    def test_stock_valuation(self):
        """Test total stock valuation calculation."""
        # 25 pcs * 500.00 = 12500.00
        self.assertEqual(self.product.total_stock_value, Decimal("12500.00"))
        # 25 pcs * 590.00 = 14750.00
        self.assertEqual(self.product.total_stock_value_with_gst, Decimal("14750.00"))

    def test_stock_status_and_low_stock(self):
        """Test low stock threshold logic and stock status text."""
        self.assertFalse(self.product.is_low_stock)
        self.assertEqual(self.product.stock_status, "In Stock")

        # Reduce stock to low stock level (<= min_stock_level of 10)
        self.product.stock = 5
        self.product.save()
        self.assertTrue(self.product.is_low_stock)
        self.assertEqual(self.product.stock_status, "Low Stock")

        # Set stock to zero
        self.product.stock = 0
        self.product.save()
        self.assertTrue(self.product.is_low_stock)
        self.assertEqual(self.product.stock_status, "Out of Stock")

    def test_model_validation_negative_price(self):
        """Test that negative price triggers ValidationError."""
        p = Product(
            name="Invalid Product",
            price=Decimal("-100.00"),
            stock=10,
            gst_rate=Decimal("18.00")
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_model_validation_negative_stock(self):
        """Test that negative stock quantity triggers ValidationError."""
        p = Product(
            name="Invalid Stock Product",
            price=Decimal("100.00"),
            stock=-5,
            gst_rate=Decimal("18.00")
        )
        with self.assertRaises(ValidationError):
            p.full_clean()


class ProductFormTestCase(TestCase):
    """
    Unit tests for Product forms.
    """

    def test_valid_product_form(self):
        """Test product form submission with valid data."""
        form_data = {
            'sku': 'PRD-9999',
            'name': 'USB-C Fast Charging Cable',
            'category': 'Electronics',
            'price': '299.00',
            'stock': '50',
            'gst_rate': '18.00',
            'hsn_code': '85444299',
            'unit': 'pcs',
            'min_stock_level': '15',
            'description': '1.5 meter braided cable',
            'is_active': True,
        }
        form = ProductForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_product_form_missing_name(self):
        """Test form invalidity when required name field is missing."""
        form_data = {
            'price': '100.00',
            'stock': '10',
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class ProductViewTestCase(TestCase):
    """
    Unit tests for Product HTML views.
    """

    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            name="Mechanical Keyboard",
            category="Electronics",
            price=Decimal("2500.00"),
            stock=12,
            gst_rate=Decimal("18.00"),
            unit="pcs",
            min_stock_level=5
        )

    def test_product_list_view(self):
        """Test product catalog list view loads cleanly."""
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_list.html')
        self.assertContains(response, "Mechanical Keyboard")

    def test_product_detail_view(self):
        """Test product detail view."""
        response = self.client.get(reverse('product_detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_detail.html')
        self.assertContains(response, "Mechanical Keyboard")

    def test_product_create_view_get_and_post(self):
        """Test product creation view."""
        response = self.client.get(reverse('product_create'))
        self.assertEqual(response.status_code, 200)

        post_data = {
            'name': 'HD Monitor 24-inch',
            'category': 'Electronics',
            'price': '12000.00',
            'stock': '8',
            'gst_rate': '18.00',
            'unit': 'pcs',
            'min_stock_level': '3',
            'is_active': True,
        }
        post_resp = self.client.post(reverse('product_create'), data=post_data)
        self.assertEqual(post_resp.status_code, 302)  # Redirects to detail view
        self.assertTrue(Product.objects.filter(name='HD Monitor 24-inch').exists())

    def test_product_update_view(self):
        """Test updating a product."""
        post_data = {
            'name': 'Mechanical Keyboard RGB',
            'category': 'Electronics',
            'price': '2800.00',
            'stock': '15',
            'gst_rate': '18.00',
            'unit': 'pcs',
            'min_stock_level': '5',
            'is_active': True,
        }
        response = self.client.post(reverse('product_edit', kwargs={'pk': self.product.pk}), data=post_data)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Mechanical Keyboard RGB')
        self.assertEqual(self.product.price, Decimal('2800.00'))

    def test_product_delete_view(self):
        """Test deleting a product."""
        response = self.client.post(reverse('product_delete', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())


class ProductApiTestCase(TestCase):
    """
    Unit tests for Product REST API endpoints.
    """

    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            name="Ergonomic Desk Chair",
            category="Office Supplies",
            price=Decimal("7500.00"),
            stock=10,
            gst_rate=Decimal("18.00"),
            unit="pcs"
        )

    def test_api_list_products(self):
        """Test GET /products/api/products/."""
        response = self.client.get(reverse('api_product_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertGreaterEqual(data['count'], 1)

    def test_api_create_product(self):
        """Test POST /products/api/products/."""
        payload = {
            'name': 'Standing Desk Converter',
            'category': 'Office Supplies',
            'price': '15000.00',
            'stock': 5,
            'gst_rate': '18.00',
            'unit': 'pcs',
            'min_stock_level': 2,
        }
        response = self.client.post(
            reverse('api_product_list'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(Product.objects.filter(name='Standing Desk Converter').exists())

    def test_api_get_product_detail(self):
        """Test GET /products/api/products/<pk>/."""
        response = self.client.get(reverse('api_product_detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['product']['name'], 'Ergonomic Desk Chair')

    def test_api_update_product(self):
        """Test PUT /products/api/products/<pk>/."""
        payload = {
            'name': 'Ergonomic Desk Chair Pro',
            'price': '8200.00',
            'stock': 12,
        }
        response = self.client.put(
            reverse('api_product_detail', kwargs={'pk': self.product.pk}),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Ergonomic Desk Chair Pro')
        self.assertEqual(self.product.price, Decimal('8200.00'))

    def test_api_delete_product(self):
        """Test DELETE /products/api/products/<pk>/."""
        response = self.client.delete(reverse('api_product_detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
