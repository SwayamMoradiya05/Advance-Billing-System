import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .forms import LoginForm
from .serializers import LoginSerializer

User = get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'johndoe'
        self.password = 'SecurePass123!'
        self.user = User.objects.create_user(
            username=self.username,
            email='john@example.com',
            password=self.password
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
        self.assertRedirects(response, reverse('login'))
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
