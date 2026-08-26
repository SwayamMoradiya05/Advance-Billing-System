import json
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from .forms import LoginForm
from .serializers import LoginSerializer, OTPRequestSerializer, OTPVerifySerializer
from .models import OTPCode, DistributorProfile

User = get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'johndoe'
        self.password = 'SecurePass123!'
        self.user = User.objects.create_user(
            username=self.username,
            email='john@example.com',
            password=self.password,
            is_staff=True
        )
        self.inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password=self.password,
            is_active=False
        )

    def test_form_valid_credentials(self):
        form = LoginForm(data={'username': self.username, 'password': self.password})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['user'], self.user)

    def test_form_invalid_password(self):
        form = LoginForm(data={'username': self.username, 'password': 'wrongpassword'})
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid username or password.', form.non_field_errors())

    def test_form_inactive_user(self):
        form = LoginForm(data={'username': 'inactive', 'password': self.password})
        self.assertFalse(form.is_valid())
        self.assertIn('This user account is inactive.', form.non_field_errors())

    def test_serializer_valid_credentials(self):
        serializer = LoginSerializer(data={'username': self.username, 'password': self.password})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.user, self.user)

    def test_serializer_invalid_credentials(self):
        serializer = LoginSerializer(data={'username': self.username, 'password': 'wrong'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_web_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password,
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_web_login_failure(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': 'badpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')

    def test_api_login_success(self):
        response = self.client.post(
            reverse('api_login'),
            data=json.dumps({'username': self.username, 'password': self.password}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message'], 'Login successful')
        self.assertEqual(data['user']['username'], self.username)

    def test_api_login_invalid_credentials(self):
        response = self.client.post(
            reverse('api_login'),
            data=json.dumps({'username': self.username, 'password': 'wrongpassword'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Invalid credentials')

    def test_api_login_inactive_user(self):
        response = self.client.post(
            reverse('api_login'),
            data=json.dumps({'username': 'inactive', 'password': self.password}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_logout(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_admin_login_sets_name_swayam(self):
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=self.password
        )
        response = self.client.post(
            reverse('api_login'),
            data=json.dumps({'username': 'admin', 'password': self.password}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['name'], 'Swayam')

        admin_user.refresh_from_db()
        self.assertEqual(admin_user.first_name, 'Swayam')


class OTPTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.email = 'john@example.com'
        self.user = User.objects.create_user(
            username='johndoe',
            email=self.email,
            password='OldPassword123!'
        )

    def test_otp_generation_and_db_storage(self):
        otp = OTPCode.generate_otp(self.email)
        self.assertEqual(OTPCode.objects.filter(email=self.email).count(), 1)
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())
        self.assertTrue(otp.is_valid())

    def test_otp_validation_success(self):
        otp = OTPCode.generate_otp(self.email)
        res = OTPCode.validate_otp(self.email, otp.code)
        self.assertTrue(res)
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_otp_validation_wrong_code(self):
        OTPCode.generate_otp(self.email)
        res = OTPCode.validate_otp(self.email, '000000')
        self.assertFalse(res)

    def test_otp_cannot_be_reused(self):
        otp = OTPCode.generate_otp(self.email)
        res1 = OTPCode.validate_otp(self.email, otp.code)
        self.assertTrue(res1)
        res2 = OTPCode.validate_otp(self.email, otp.code)
        self.assertFalse(res2)

    def test_expired_otp(self):
        otp = OTPCode.objects.create(
            email=self.email,
            code='123456',
            is_used=False
        )
        OTPCode.objects.filter(pk=otp.pk).update(
            created_at=timezone.now() - timedelta(minutes=15)
        )
        otp.refresh_from_db()
        self.assertFalse(otp.is_valid())
        self.assertFalse(OTPCode.validate_otp(self.email, '123456'))

    def test_api_request_otp(self):
        response = self.client.post(
            reverse('api_request_otp'),
            data=json.dumps({'email': self.email}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message'], 'OTP generated successfully')
        self.assertIn('otp', data)
        self.assertTrue(OTPCode.objects.filter(email=self.email).exists())

    def test_api_verify_otp_success_resets_password(self):
        otp = OTPCode.generate_otp(self.email)
        new_pass = 'NewSecurePass123!'
        response = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({
                'email': self.email,
                'code': otp.code,
                'new_password': new_pass
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_pass))

    def test_api_verify_otp_invalid_code(self):
        response = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({
                'email': self.email,
                'code': '999999'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Invalid or expired OTP')


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_data = {
            'full_name': 'David Miller',
            'email': 'david.m@apexsupplies.com',
            'phone': '+1 555-019-8842',
            'company_name': 'Apex Global Supplies',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'agree_terms': 'on',
        }

    def test_distributor_registration_stores_data_in_db_and_redirects_to_login(self):
        response = self.client.post(reverse('distributor_register'), self.valid_data, follow=True)
        
        # 1. Assert redirection to distributor_login
        self.assertRedirects(response, reverse('distributor_login'))
        
        # 2. Assert User stored in DB
        user = User.objects.filter(email='david.m@apexsupplies.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'David')
        self.assertEqual(user.last_name, 'Miller')
        self.assertTrue(user.check_password('SecurePassword123!'))

        # 3. Assert DistributorProfile stored in DB
        profile = DistributorProfile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.phone, '+1 555-019-8842')
        self.assertEqual(profile.company_name, 'Apex Global Supplies')
        self.assertTrue(profile.distributor_id.startswith('DIST-'))

        # 4. Assert Success Message in response
        messages = list(response.context['messages'])
        self.assertTrue(any('Distributor account created successfully' in str(m) for m in messages))

    def test_api_distributor_registration_stores_data_in_db(self):
        api_data = {
            'full_name': 'Sarah Connor',
            'email': 'sarah@cyberdyne.com',
            'phone': '+1 555-019-9999',
            'company_name': 'Cyberdyne Systems',
            'password': 'CyberPassword123!',
            'confirm_password': 'CyberPassword123!',
            'agree_terms': True,
        }
        response = self.client.post(
            reverse('api_register'),
            data=json.dumps(api_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        res_json = response.json()
        self.assertIn('distributor_id', res_json)
        self.assertEqual(res_json['redirect_url'], '/distributor-login/')

        # Assert data stored in database
        user = User.objects.filter(email='sarah@cyberdyne.com').first()
        self.assertIsNotNone(user)
        self.assertTrue(DistributorProfile.objects.filter(user=user).exists())

    def test_distributor_registration_duplicate_email_error(self):
        User.objects.create_user(username='existing', email='david.m@apexsupplies.com', password='pass')
        response = self.client.post(reverse('distributor_register'), self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email address is already registered.')
        self.assertEqual(User.objects.filter(email='david.m@apexsupplies.com').count(), 1)

    def test_distributor_registration_password_mismatch_error(self):
        data = self.valid_data.copy()
        data['confirm_password'] = 'Mismatch123!'
        response = self.client.post(reverse('distributor_register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match.')

    def test_login_with_distributor_email_and_id(self):
        # Register user and profile
        self.client.post(reverse('distributor_register'), self.valid_data)
        user = User.objects.get(email='david.m@apexsupplies.com')
        distributor_id = user.distributor_profile.distributor_id

        # Test login via email
        res_email = self.client.post(reverse('distributor_login'), {
            'username': 'david.m@apexsupplies.com',
            'password': 'SecurePassword123!',
        })
        self.assertRedirects(res_email, reverse('distributor_dashboard'))

        # Test login via distributor_id
        res_id = self.client.post(reverse('distributor_login'), {
            'username': distributor_id,
            'password': 'SecurePassword123!',
        })
        self.assertRedirects(res_id, reverse('distributor_dashboard'))


class DistributorProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'distributor_user'
        self.password = 'DistPass123!'
        self.user = User.objects.create_user(
            username=self.username,
            email='dist@partner.com',
            password=self.password,
            first_name='Alex',
            last_name='Vance'
        )
        self.profile = DistributorProfile.objects.create(
            user=self.user,
            phone='+1 555-019-7777',
            company_name='Vance Logistics',
            distributor_id='DIST-9999',
            credit_limit=75000.00
        )

    def test_distributor_profile_view_requires_login(self):
        response = self.client.get(reverse('distributor_profile'))
        self.assertEqual(response.status_code, 302)

    def test_distributor_profile_view_renders_profile(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('distributor_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alex Vance')
        self.assertContains(response, 'dist@partner.com')
        self.assertContains(response, 'Vance Logistics')
        self.assertContains(response, 'DIST-9999')

    def test_distributor_profile_update_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('distributor_profile'), {
            'full_name': 'Alex Vance Updated',
            'email': 'alex.updated@partner.com',
            'phone': '+1 555-019-8888',
            'company_name': 'Vance Global Corp',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()

        self.assertEqual(self.user.first_name, 'Alex')
        self.assertEqual(self.user.last_name, 'Vance Updated')
        self.assertEqual(self.user.email, 'alex.updated@partner.com')
        self.assertEqual(self.profile.phone, '+1 555-019-8888')
        self.assertEqual(self.profile.company_name, 'Vance Global Corp')

    def test_api_distributor_profile_get_and_update(self):
        self.client.login(username=self.username, password=self.password)
        # GET profile
        get_res = self.client.get(reverse('api_distributor_profile'))
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.json()
        self.assertEqual(get_data['distributor_id'], 'DIST-9999')
        self.assertEqual(get_data['email'], 'dist@partner.com')

        # POST update profile
        update_data = {
            'full_name': 'Alexander Vance',
            'email': 'alexander@partner.com',
            'phone': '+1 555-019-1111',
            'company_name': 'Vance Enterprises',
        }
        post_res = self.client.post(
            reverse('api_distributor_profile'),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(post_res.status_code, 200)
        res_json = post_res.json()
        self.assertEqual(res_json['profile']['full_name'], 'Alexander Vance')
        self.assertEqual(res_json['profile']['company_name'], 'Vance Enterprises')


