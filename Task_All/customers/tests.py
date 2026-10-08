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

    def test_customer_update_view_get(self):
        response = self.client.get(reverse('customer_update', kwargs={'pk': self.customer1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Customer: Alpha Corp")
        self.assertContains(response, "alpha@corp.com")

    def test_customer_update_view_post(self):
        post_data = {
            'name': 'Alpha Corp Updated',
            'email': 'alpha.updated@corp.com',
            'phone': '5551234567',
            'address': '789 Market Street',
            'country': 'India',
            'credit_limit': '60000.00',
            'outstanding_balance': '500.00',
            'is_active': True,
        }
        response = self.client.post(reverse('customer_update', kwargs={'pk': self.customer1.pk}), post_data)
        self.assertEqual(response.status_code, 302)
        self.customer1.refresh_from_db()
        self.assertEqual(self.customer1.name, 'Alpha Corp Updated')
        self.assertEqual(self.customer1.email, 'alpha.updated@corp.com')
        self.assertEqual(self.customer1.credit_limit, Decimal('60000.00'))


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

    def test_api_customer_update_put(self):
        payload = {
            'name': 'API Client Updated',
            'email': 'api.updated@client.com',
            'phone': '1234567890',
            'address': '1 Enterprise Way Updated',
            'credit_limit': '35000.00'
        }
        response = self.client.put(
            reverse('api_customer_detail', kwargs={'pk': self.customer.pk}),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, 'API Client Updated')
        self.assertEqual(self.customer.email, 'api.updated@client.com')


User = get_user_model()


class DistributorCustomerApiTest(TestCase):
    """Tests for the distributor-scoped Customer registration API endpoints."""

    def setUp(self):
        self.client = Client()

        # Create a Distributor user (non-staff)
        self.distributor = User.objects.create_user(
            username='dist_test_user',
            email='dist@testdist.com',
            password='DistPass123!',
            is_staff=False,
            is_superuser=False,
        )

        # Create an Admin/Staff user (should be blocked)
        self.admin = User.objects.create_user(
            username='admin_test_user2',
            email='admin2@test.com',
            password='AdminPass123!',
            is_staff=True,
        )

        # Create a customer already linked to this distributor
        self.existing_customer = Customer.objects.create(
            name='Existing Dist Customer',
            email='existing_dist@test.com',
            phone='9876543210',
            address='5 Dist Road',
            distributor=self.distributor,
        )

        # A customer belonging to no distributor (should be invisible to this distributor)
        self.other_customer = Customer.objects.create(
            name='Other Customer',
            email='other@test.com',
            phone='1112223333',
            address='99 Other Lane',
        )

        self.valid_payload = {
            'name': 'New Dist Customer',
            'email': 'new_dist_customer@test.com',
            'phone': '5551234567',
            'address': '12 Commerce St',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'country': 'India',
        }

    # ---- GET (list own customers) ----

    def test_distributor_can_list_own_customers(self):
        self.client.login(username='dist_test_user', password='DistPass123!')
        response = self.client.get(reverse('api_distributor_customer_list_create'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['distributor'], 'dist_test_user')
        # Only see own customer, not other_customer
        codes = [c['customer_code'] for c in data['customers']]
        self.assertIn(self.existing_customer.customer_code, codes)
        self.assertNotIn(self.other_customer.customer_code, codes)

    def test_unauthenticated_cannot_access_distributor_api(self):
        response = self.client.get(reverse('api_distributor_customer_list_create'))
        self.assertEqual(response.status_code, 302)  # login redirect

    def test_admin_blocked_from_distributor_api(self):
        self.client.login(username='admin_test_user2', password='AdminPass123!')
        response = self.client.get(reverse('api_distributor_customer_list_create'))
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data['status'], 'error')

    # ---- POST (register new customer) ----

    def test_distributor_can_register_customer(self):
        self.client.login(username='dist_test_user', password='DistPass123!')
        response = self.client.post(
            reverse('api_distributor_customer_list_create'),
            data=json.dumps(self.valid_payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['customer']['name'], 'New Dist Customer')
        # Verify linked to distributor
        created = Customer.objects.get(email='new_dist_customer@test.com')
        self.assertEqual(created.distributor, self.distributor)

    def test_distributor_register_customer_missing_fields(self):
        self.client.login(username='dist_test_user', password='DistPass123!')
        response = self.client.post(
            reverse('api_distributor_customer_list_create'),
            data=json.dumps({'name': 'No Email'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('email', data['errors'])

    # ---- GET detail ----

    def test_distributor_can_get_own_customer_detail(self):
        self.client.login(username='dist_test_user', password='DistPass123!')
        response = self.client.get(
            reverse('api_distributor_customer_detail', kwargs={'pk': self.existing_customer.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['customer']['email'], 'existing_dist@test.com')

    def test_distributor_cannot_get_other_customer(self):
        self.client.login(username='dist_test_user', password='DistPass123!')
        response = self.client.get(
            reverse('api_distributor_customer_detail', kwargs={'pk': self.other_customer.pk})
        )
        self.assertEqual(response.status_code, 404)

    # ---- PUT (update own customer) ----

    def test_distributor_can_update_own_customer(self):
        self.client.login(username='dist_test_user', password='DistPass123!')
        payload = {
            'name': 'Updated Dist Customer',
            'email': 'existing_dist@test.com',
            'phone': '9876543210',
            'address': '5 Dist Road Updated',
        }
        response = self.client.put(
            reverse('api_distributor_customer_detail', kwargs={'pk': self.existing_customer.pk}),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.existing_customer.refresh_from_db()
        self.assertEqual(self.existing_customer.name, 'Updated Dist Customer')

    # ---- DELETE ----

    def test_distributor_can_delete_own_customer(self):
        self.client.login(username='dist_test_user', password='DistPass123!')
        response = self.client.delete(
            reverse('api_distributor_customer_detail', kwargs={'pk': self.existing_customer.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.filter(pk=self.existing_customer.pk).exists())

