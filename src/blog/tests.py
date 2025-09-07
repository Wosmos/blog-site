from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.sessions.models import Session


class AuthenticationTestCase(TestCase):
    """Test cases for blog admin authentication system."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.username = 'testadmin'
        self.password = 'testpass123'
        self.email = 'admin@test.com'
        
        # Create test user
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            is_active=True
        )
        
        # Create inactive user for testing
        self.inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@test.com',
            password='testpass123',
            is_active=False
        )
        
        # URLs
        self.login_url = reverse('blog:admin_login')
        self.logout_url = reverse('blog:admin_logout')
        self.dashboard_url = reverse('blog:admin_dashboard')
    
    def test_login_page_loads(self):
        """Test that login page loads correctly."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blog Admin Login')
        self.assertContains(response, 'username')
        self.assertContains(response, 'password')
        self.assertContains(response, 'csrf')
    
    def test_successful_login(self):
        """Test successful login with valid credentials."""
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password
        })
        
        # Should redirect to dashboard
        self.assertRedirects(response, self.dashboard_url)
        
        # User should be logged in
        self.assertTrue(self.client.session.get('_auth_user_id'))
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Welcome back' in str(m) for m in messages))
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': 'wrongpassword'
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
        
        # User should not be logged in
        self.assertFalse(self.client.session.get('_auth_user_id'))
    
    def test_login_with_inactive_user(self):
        """Test login with inactive user account."""
        response = self.client.post(self.login_url, {
            'username': 'inactive',
            'password': 'testpass123'
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        
        # Check for error message (Django's authenticate returns None for inactive users)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Invalid username or password' in str(m) for m in messages))
        
        # User should not be logged in
        self.assertFalse(self.client.session.get('_auth_user_id'))
    
    def test_login_with_missing_fields(self):
        """Test login with missing username or password."""
        # Missing password
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please provide both username and password')
        
        # Missing username
        response = self.client.post(self.login_url, {
            'username': '',
            'password': self.password
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please provide both username and password')
    
    def test_login_redirect_for_authenticated_user(self):
        """Test that authenticated users are redirected from login page."""
        # Log in user
        self.client.login(username=self.username, password=self.password)
        
        # Try to access login page
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.dashboard_url)
    
    def test_login_with_next_parameter(self):
        """Test login redirect to next URL parameter."""
        next_url = '/blog/admin/some-page/'
        response = self.client.post(f'{self.login_url}?next={next_url}', {
            'username': self.username,
            'password': self.password
        })
        
        # Should redirect to next URL
        self.assertRedirects(response, next_url, fetch_redirect_response=False)
    
    def test_logout_functionality(self):
        """Test logout functionality."""
        # Log in user first
        self.client.login(username=self.username, password=self.password)
        self.assertTrue(self.client.session.get('_auth_user_id'))
        
        # Logout
        response = self.client.get(self.logout_url)
        
        # Should redirect to login page
        self.assertRedirects(response, self.login_url)
        
        # User should be logged out
        self.assertFalse(self.client.session.get('_auth_user_id'))
        
        # Check logout message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('successfully logged out' in str(m) for m in messages))
    
    def test_logout_requires_authentication(self):
        """Test that logout requires authentication."""
        # Try to logout without being logged in
        response = self.client.get(self.logout_url)
        
        # Should redirect to login page
        self.assertRedirects(response, f'{self.login_url}?next={self.logout_url}')


class AuthorizationTestCase(TestCase):
    """Test cases for blog admin authorization system."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_active=True
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_active=True,
            is_staff=True
        )
        
        # Create inactive user
        self.inactive_user = User.objects.create_user(
            username='inactive',
            password='testpass123',
            is_active=False
        )
        
        self.dashboard_url = reverse('blog:admin_dashboard')
        self.login_url = reverse('blog:admin_login')
    
    def test_dashboard_requires_authentication(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(self.dashboard_url)
        
        # Should redirect to login with next parameter
        expected_url = f'{self.login_url}?next={self.dashboard_url}'
        self.assertRedirects(response, expected_url)
    
    def test_dashboard_access_for_authenticated_user(self):
        """Test dashboard access for authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blog Admin Dashboard')
        self.assertContains(response, 'testuser')
    
    def test_dashboard_access_for_inactive_user(self):
        """Test dashboard access denied for inactive user."""
        # Try to access dashboard with inactive user session
        session = self.client.session
        session['_auth_user_id'] = str(self.inactive_user.id)
        session.save()
        
        response = self.client.get(self.dashboard_url)
        # Should redirect to login with next parameter
        expected_url = f'{self.login_url}?next={self.dashboard_url}'
        self.assertRedirects(response, expected_url)
    
    def test_admin_required_decorator(self):
        """Test admin_required decorator functionality."""
        from blog.auth_views import admin_required
        from django.http import HttpResponse
        
        @admin_required
        def test_view(request):
            return HttpResponse('Success')
        
        # Test with unauthenticated user
        response = test_view(self.client.request().wsgi_request)
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Test with authenticated user
        self.client.login(username='testuser', password='testpass123')
        request = self.client.request().wsgi_request
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_staff_required_decorator(self):
        """Test staff_required decorator functionality."""
        from blog.auth_views import staff_required
        from django.http import HttpResponse
        
        @staff_required
        def test_view(request):
            return HttpResponse('Success')
        
        # Test with regular user
        self.client.login(username='testuser', password='testpass123')
        request = self.client.request().wsgi_request
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Test with staff user
        self.client.login(username='staffuser', password='testpass123')
        request = self.client.request().wsgi_request
        request.user = self.staff_user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)


class SessionSecurityTestCase(TestCase):
    """Test cases for session security and CSRF protection."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.login_url = reverse('blog:admin_login')
    
    def test_csrf_protection_on_login(self):
        """Test CSRF protection on login form."""
        # Disable CSRF middleware for this test by using enforce_csrf_checks=True
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        
        # POST without CSRF token should fail
        response = client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_session_creation_on_login(self):
        """Test that session is created on successful login."""
        initial_session_count = Session.objects.count()
        
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Session should be created
        self.assertGreater(Session.objects.count(), initial_session_count)
        
        # Session should contain user ID
        self.assertTrue(self.client.session.get('_auth_user_id'))
    
    def test_session_cleanup_on_logout(self):
        """Test that session is properly cleaned up on logout."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        session_key = self.client.session.session_key
        
        # Logout
        logout_url = reverse('blog:admin_logout')
        self.client.get(logout_url)
        
        # Session should be cleared
        self.assertFalse(self.client.session.get('_auth_user_id'))


class SecurityHeadersTestCase(TestCase):
    """Test cases for security headers and configurations."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.login_url = reverse('blog:admin_login')
    
    def test_login_page_security_headers(self):
        """Test that login page includes proper security headers."""
        response = self.client.get(self.login_url)
        
        # Check for X-Frame-Options (clickjacking protection)
        self.assertIn('X-Frame-Options', response)
        
        # Check that CSRF token is present in form
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_form_validation_javascript(self):
        """Test that client-side validation is present."""
        response = self.client.get(self.login_url)
        
        # Check for validation JavaScript
        self.assertContains(response, 'addEventListener')
        self.assertContains(response, 'is-invalid')
        self.assertContains(response, 'preventDefault')
