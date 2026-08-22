import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from customers.models import Customer
from customers.forms import CustomerForm
from customers.serializers import CustomerSerializer

User = get_user_model()


class CustomerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testdistributor", password="password123")
        self.customer = Customer.objects.create(
            name="Acme Corp",
            email="contact@acme.com",
            phone="+1 555-019-1000",
            company_name="Acme Corporation",
            address="100 Innovation Way",
            city="Metropolis",
            state="NY",
            postal_code="10001",
            country="USA",
            credit_limit=Decimal("50000.00"),
            outstanding_balance=Decimal("12000.00"),
            distributor=self.user,
        )

    def test_customer_creation_and_auto_code(self):
        self.assertTrue(self.customer.customer_code.startswith("CUST-"))
        self.assertEqual(str(self.customer), "Acme Corp - Acme Corporation (" + self.customer.customer_code + ")")
        self.assertTrue(self.customer.is_active)

    def test_available_credit_calculation(self):
        self.assertEqual(self.customer.available_credit, Decimal("38000.00"))
        self.assertTrue(self.customer.has_available_credit)

    def test_full_address_property(self):
        self.assertEqual(self.customer.full_address, "100 Innovation Way, Metropolis, NY, 10001, USA")

    def test_phone_validation_error(self):
        invalid_customer = Customer(
            name="Invalid Phone",
            email="invalid@test.com",
            phone="abc-12345",
            address="123 Street"
        )
        with self.assertRaises(ValidationError):
            invalid_customer.full_clean()

    def test_negative_credit_limit_validation(self):
        invalid_customer = Customer(
            name="Negative Credit",
            email="neg@test.com",
            phone="1234567890",
            address="123 Street",
            credit_limit=Decimal("-100.00")
        )
        with self.assertRaises(ValidationError):
            invalid_customer.full_clean()


class CustomerFormTest(TestCase):
    def test_valid_customer_form(self):
        form_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '9876543210',
            'company_name': 'Doe Logistics',
            'address': '456 Commercial Rd',
            'city': 'Chicago',
            'state': 'IL',
            'postal_code': '60601',
            'country': 'USA',
            'tax_id': 'TAX-998877',
            'credit_limit': '25000.00',
            'outstanding_balance': '0.00',
            'is_active': True,
            'notes': 'Preferred customer',
        }
        form = CustomerForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email_customer_form(self):
        form_data = {
            'name': 'John Doe',
            'email': 'not-an-email',
            'phone': '9876543210',
            'address': '456 Commercial Rd',
        }
        form = CustomerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class CustomerViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="adminuser", password="securepassword123")
        self.client.force_login(self.user)
        self.customer1 = Customer.objects.create(
            name="Alpha Corp",
            email="alpha@corp.com",
            phone="5551234567",
            company_name="Alpha Tech",
            address="789 Market Street",
            city="Mumbai",
            is_active=True
        )
        self.customer2 = Customer.objects.create(
            name="Beta Traders",
            email="beta@traders.com",
            phone="9876543210",
            company_name="Beta Logistics",
            address="123 Industrial Park",
            city="Delhi",
            is_active=False
        )

    def test_customer_list_view(self):
        response = self.client.get(reverse('customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Corp")
        self.assertContains(response, "Beta Traders")

    def test_customer_list_search_by_name(self):
        response = self.client.get(reverse('customer_list') + '?q=Alpha')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Corp")
        self.assertNotContains(response, "Beta Traders")

    def test_customer_list_search_by_city(self):
        response = self.client.get(reverse('customer_list') + '?q=Delhi')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beta Traders")
        self.assertNotContains(response, "Alpha Corp")

    def test_customer_list_filter_by_status(self):
        response = self.client.get(reverse('customer_list') + '?status=active')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Corp")
        self.assertNotContains(response, "Beta Traders")

        response_inactive = self.client.get(reverse('customer_list') + '?status=inactive')
        self.assertEqual(response_inactive.status_code, 200)
        self.assertContains(response_inactive, "Beta Traders")
        self.assertNotContains(response_inactive, "Alpha Corp")

    def test_customer_list_sorting(self):
        response = self.client.get(reverse('customer_list') + '?sort=name')
        self.assertEqual(response.status_code, 200)
        customers_in_context = list(response.context['customers'])
        self.assertEqual(customers_in_context[0].name, "Alpha Corp")
        self.assertEqual(customers_in_context[1].name, "Beta Traders")

    def test_customer_detail_view(self):
        response = self.client.get(reverse('customer_detail', kwargs={'pk': self.customer1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Corp")

    def test_customer_create_view(self):
        post_data = {
            'name': 'New Web Customer',
            'email': 'newweb@customer.com',
            'phone': '5559876543',
            'address': '321 Ocean Drive',
            'country': 'India',
            'credit_limit': '15000.00',
            'outstanding_balance': '0.00',
            'is_active': True,
        }
        response = self.client.post(reverse('customer_create'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(email='newweb@customer.com').exists())



class CustomerApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            name="API Client",
            email="api@client.com",
            phone="1234567890",
            address="1 Enterprise Way"
        )

    def test_api_customer_list(self):
        response = self.client.get(reverse('api_customer_list_create'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertGreaterEqual(data['count'], 1)

    def test_api_customer_create(self):
        payload = {
            'name': 'REST API Customer',
            'email': 'restapi@customer.com',
            'phone': '9998887770',
            'address': '55 Tech Park',
            'credit_limit': '20000.00',
        }
        response = self.client.post(
            reverse('api_customer_list_create'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['customer']['name'], 'REST API Customer')

    def test_api_customer_detail(self):
        response = self.client.get(reverse('api_customer_detail', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['customer']['email'], 'api@client.com')
