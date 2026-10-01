"""
Day 2 Authentication Test Suite
================================
Tests for: Registration, Login, Logout, JWT, Profile CRUD, Protected Routes.
All tests use SQLite (test DB) — Oracle is not available in CI.

Run with:
    python manage.py test apps.accounts --verbosity=2
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import UserProfile, UserRole


# ─── Helper ─────────────────────────────────────────────────────────────────

def make_user(username='testuser', email='test@example.com', password='Secure@123!',
              role=UserRole.CUSTOMER, first_name='Test', last_name='User'):
    """Create a test user with an attached profile."""
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    UserProfile.objects.create(user=user, role=role)
    return user


# ─── Model Tests ─────────────────────────────────────────────────────────────

class UserProfileModelTest(TestCase):
    """Tests for the UserProfile model."""

    def setUp(self):
        self.customer = make_user(role=UserRole.CUSTOMER)
        self.provider = make_user(
            username='provider', email='provider@example.com',
            role=UserRole.PARKING_PROVIDER
        )

    def test_profile_created_with_correct_role_customer(self):
        """UserProfile stores the CUSTOMER role correctly."""
        self.assertEqual(self.customer.profile.role, UserRole.CUSTOMER)

    def test_profile_created_with_correct_role_provider(self):
        """UserProfile stores the PARKING_PROVIDER role correctly."""
        self.assertEqual(self.provider.profile.role, UserRole.PARKING_PROVIDER)

    def test_is_customer_property(self):
        """is_customer returns True only for CUSTOMER role."""
        self.assertTrue(self.customer.profile.is_customer)
        self.assertFalse(self.provider.profile.is_customer)

    def test_is_parking_provider_property(self):
        """is_parking_provider returns True only for PARKING_PROVIDER role."""
        self.assertTrue(self.provider.profile.is_parking_provider)
        self.assertFalse(self.customer.profile.is_parking_provider)

    def test_str_representation(self):
        """UserProfile __str__ includes username and role."""
        self.assertIn('testuser', str(self.customer.profile))
        self.assertIn('Customer', str(self.customer.profile))

    def test_phone_number_defaults_to_empty_string(self):
        """Phone number field defaults to empty string."""
        self.assertEqual(self.customer.profile.phone_number, '')

    def test_created_at_is_auto_set(self):
        """created_at is automatically populated."""
        self.assertIsNotNone(self.customer.profile.created_at)


# ─── Registration API Tests ───────────────────────────────────────────────────

class RegisterAPIViewTest(TestCase):
    """Tests for POST /api/auth/register/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('accounts:api-register')

    def _valid_payload(self, **overrides):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'Secure@123!',
            'confirm_password': 'Secure@123!',
            'role': 'CUSTOMER',
        }
        data.update(overrides)
        return data

    def test_register_customer_returns_201(self):
        """Valid customer registration returns HTTP 201 with tokens."""
        response = self.client.post(self.url, self._valid_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_register_parking_provider_returns_201(self):
        """Valid parking provider registration returns HTTP 201."""
        payload = self._valid_payload(
            username='provider', email='provider@example.com',
            role='PARKING_PROVIDER'
        )
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_creates_user_profile(self):
        """Registration creates a UserProfile for the new user."""
        self.client.post(self.url, self._valid_payload(), format='json')
        # The API serializer uses email as the username field
        user = User.objects.get(username='new@example.com')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.role, UserRole.CUSTOMER)

    def test_register_duplicate_username_returns_400(self):
        """Duplicate email (used as username) returns HTTP 400."""
        # The API uses email as both email and username — duplicate email should fail
        make_user(username='new@example.com', email='new@example.com')
        response = self.client.post(self.url, self._valid_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email_returns_400(self):
        """Duplicate email returns HTTP 400."""
        make_user(username='existinguser', email='new@example.com')
        response = self.client.post(self.url, self._valid_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch_returns_400(self):
        """Mismatched passwords return HTTP 400."""
        payload = self._valid_payload(confirm_password='WrongPassword1!')
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_role_returns_400(self):
        """Invalid role value returns HTTP 400."""
        payload = self._valid_payload(role='ADMIN')
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_required_field_returns_400(self):
        """Missing required field (email) returns HTTP 400."""
        payload = self._valid_payload()
        del payload['email']
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─── Login API Tests ──────────────────────────────────────────────────────────

class LoginAPIViewTest(TestCase):
    """Tests for POST /api/auth/login/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('accounts:api-login')
        self.user = make_user()

    def test_login_with_valid_credentials_returns_200(self):
        """Valid credentials return HTTP 200 with JWT tokens."""
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'password': 'Secure@123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)

    def test_login_response_contains_role(self):
        """Login response includes user role."""
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'password': 'Secure@123!',
        }, format='json')
        self.assertIn('role', response.data['user'])
        self.assertEqual(response.data['user']['role'], 'CUSTOMER')

    def test_login_with_wrong_password_returns_401(self):
        """Wrong password returns HTTP 401."""
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'password': 'WrongPassword!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_nonexistent_email_returns_401(self):
        """Non-existent email returns HTTP 401."""
        response = self.client.post(self.url, {
            'email': 'ghost@example.com',
            'password': 'Secure@123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user_returns_401(self):
        """Inactive user cannot login."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'password': 'Secure@123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ─── Profile API Tests ────────────────────────────────────────────────────────

class ProfileAPIViewTest(TestCase):
    """Tests for GET/PUT /api/auth/profile/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('accounts:api-profile')
        self.user = make_user()

    def _authenticate(self):
        """Obtain JWT and authenticate the test client."""
        response = self.client.post(reverse('accounts:api-login'), {
            'email': 'test@example.com',
            'password': 'Secure@123!',
        }, format='json')
        token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_get_profile_unauthenticated_returns_401(self):
        """GET profile without authentication returns 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_authenticated_returns_200(self):
        """Authenticated GET returns user profile data."""
        self._authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['username'], 'testuser')

    def test_put_profile_updates_name(self):
        """PUT profile updates first_name and last_name."""
        self._authenticate()
        response = self.client.put(self.url, {
            'first_name': 'Updated',
            'last_name': 'Name',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_put_profile_updates_phone_number(self):
        """PUT profile updates phone_number on UserProfile."""
        self._authenticate()
        response = self.client.put(self.url, {
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+94771234567',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone_number, '+94771234567')


# ─── Logout API Tests ─────────────────────────────────────────────────────────

class LogoutAPIViewTest(TestCase):
    """Tests for POST /api/auth/logout/"""

    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def _get_tokens(self):
        response = self.client.post(reverse('accounts:api-login'), {
            'email': 'test@example.com',
            'password': 'Secure@123!',
        }, format='json')
        return response.data['tokens']

    def test_logout_unauthenticated_returns_401(self):
        """Logout without auth header returns 401."""
        response = self.client.post(reverse('accounts:api-logout'), {
            'refresh': 'sometoken',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_valid_refresh_returns_200(self):
        """Logout with a valid refresh token returns 200."""
        tokens = self._get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.post(reverse('accounts:api-logout'), {
            'refresh': tokens['refresh'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_without_refresh_returns_400(self):
        """Logout without refresh token body returns 400."""
        tokens = self._get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.post(reverse('accounts:api-logout'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─── Web UI View Tests ────────────────────────────────────────────────────────

class AuthWebViewsTest(TestCase):
    """Tests for web-rendered registration, login, dashboard, profile views."""

    def setUp(self):
        self.client = Client()
        self.user = make_user()

    def test_register_page_get_returns_200(self):
        """GET /register/ returns 200 for anonymous user."""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_get_returns_200(self):
        """GET /login/ returns 200 for anonymous user."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirects_unauthenticated(self):
        """GET /dashboard/ redirects anonymous user to login."""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertIn(response.status_code, [301, 302])

    def test_profile_redirects_unauthenticated(self):
        """GET /profile/ redirects anonymous user to login."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertIn(response.status_code, [301, 302])

    def test_register_page_redirects_authenticated_user(self):
        """Authenticated user accessing /register/ is redirected to dashboard."""
        self.client.login(username='testuser', password='Secure@123!')
        response = self.client.get(reverse('accounts:register'))
        self.assertIn(response.status_code, [301, 302])

    def test_login_page_redirects_authenticated_user(self):
        """Authenticated user accessing /login/ is redirected to dashboard."""
        self.client.login(username='testuser', password='Secure@123!')
        response = self.client.get(reverse('accounts:login'))
        self.assertIn(response.status_code, [301, 302])

    def test_dashboard_accessible_when_authenticated(self):
        """Authenticated user can access /dashboard/."""
        self.client.login(username='testuser', password='Secure@123!')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_profile_accessible_when_authenticated(self):
        """Authenticated user can access /profile/."""
        self.client.login(username='testuser', password='Secure@123!')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_web_login_with_valid_credentials(self):
        """POST /login/ with valid credentials redirects to dashboard."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'test@example.com',
            'password': 'Secure@123!',
        }, follow=False)
        self.assertIn(response.status_code, [301, 302])

    def test_web_logout_invalidates_session(self):
        """POST /logout/ logs the user out and redirects."""
        self.client.login(username='testuser', password='Secure@123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertIn(response.status_code, [301, 302])
        # Verify session is cleared — dashboard should now redirect
        dashboard_response = self.client.get(reverse('accounts:dashboard'))
        self.assertIn(dashboard_response.status_code, [301, 302])

    def test_profile_update_via_post(self):
        """POST /profile/ with valid data updates user info."""
        self.client.login(username='testuser', password='Secure@123!')
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'phone_number': '+94771112233',
        })
        self.assertIn(response.status_code, [200, 301, 302])
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedFirst')


# ─── Token Refresh Test ───────────────────────────────────────────────────────

class TokenRefreshTest(TestCase):
    """Tests for POST /api/auth/token/refresh/"""

    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def test_token_refresh_with_valid_token_returns_200(self):
        """Valid refresh token produces a new access token."""
        login_response = self.client.post(reverse('accounts:api-login'), {
            'email': 'test@example.com',
            'password': 'Secure@123!',
        }, format='json')
        refresh_token = login_response.data['tokens']['refresh']

        response = self.client.post(reverse('accounts:api-token-refresh'), {
            'refresh': refresh_token,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_with_invalid_token_returns_401(self):
        """Invalid refresh token returns 401."""
        response = self.client.post(reverse('accounts:api-token-refresh'), {
            'refresh': 'thisisnotavalidtoken',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
