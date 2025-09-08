from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.sessions.models import Session
from .models import BlogPost


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


class BlogListViewTestCase(TestCase):
    """Test cases for blog list view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='author1',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        self.user2 = User.objects.create_user(
            username='author2',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Create test blog posts
        self.post1 = BlogPost.objects.create(
            title='First Blog Post',
            content='This is the content of the first blog post.',
            excerpt='First post excerpt',
            status='published',
            author=self.user1
        )
        
        self.post2 = BlogPost.objects.create(
            title='Second Blog Post',
            content='This is the content of the second blog post.',
            excerpt='Second post excerpt',
            status='draft',
            author=self.user2
        )
        
        self.post3 = BlogPost.objects.create(
            title='Third Blog Post',
            content='This is the content of the third blog post.',
            status='published',
            author=self.user1
        )
        
        # URLs
        self.list_url = reverse('blog:list')
        self.login_url = reverse('blog:admin_login')
    
    def test_blog_list_requires_authentication(self):
        """Test that blog list view requires authentication."""
        response = self.client.get(self.list_url)
        
        # Should redirect to login with next parameter
        expected_url = f'{self.login_url}?next={self.list_url}'
        self.assertRedirects(response, expected_url)
    
    def test_blog_list_displays_posts(self):
        """Test that blog list view displays all posts."""
        self.client.login(username='author1', password='testpass123')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that all posts are displayed
        self.assertContains(response, 'First Blog Post')
        self.assertContains(response, 'Second Blog Post')
        self.assertContains(response, 'Third Blog Post')
        
        # Check that authors are displayed
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Jane Smith')
        
        # Check that status badges are displayed
        self.assertContains(response, 'Published')
        self.assertContains(response, 'Draft')
    
    def test_blog_list_pagination(self):
        """Test pagination functionality."""
        # Create more posts to test pagination (need more than 10)
        for i in range(15):
            BlogPost.objects.create(
                title=f'Test Post {i}',
                content=f'Content for test post {i}',
                status='published',
                author=self.user1
            )
        
        self.client.login(username='author1', password='testpass123')
        
        # Test first page
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Should have pagination
        self.assertContains(response, 'pagination')
        self.assertContains(response, 'Next')
        
        # Test second page
        response = self.client.get(f'{self.list_url}?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Previous')
    
    def test_blog_list_search_functionality(self):
        """Test search functionality."""
        self.client.login(username='author1', password='testpass123')
        
        # Search by title
        response = self.client.get(f'{self.list_url}?search=First')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Blog Post')
        self.assertNotContains(response, 'Second Blog Post')
        
        # Search by content
        response = self.client.get(f'{self.list_url}?search=second')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Second Blog Post')
        self.assertNotContains(response, 'First Blog Post')
        
        # Search by author
        response = self.client.get(f'{self.list_url}?search=Jane')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Second Blog Post')
        self.assertNotContains(response, 'First Blog Post')
    
    def test_blog_list_status_filter(self):
        """Test status filtering functionality."""
        self.client.login(username='author1', password='testpass123')
        
        # Filter by published status
        response = self.client.get(f'{self.list_url}?status=published')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Blog Post')
        self.assertContains(response, 'Third Blog Post')
        self.assertNotContains(response, 'Second Blog Post')
        
        # Filter by draft status
        response = self.client.get(f'{self.list_url}?status=draft')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Second Blog Post')
        self.assertNotContains(response, 'First Blog Post')
        self.assertNotContains(response, 'Third Blog Post')
    
    def test_blog_list_combined_search_and_filter(self):
        """Test combined search and filter functionality."""
        self.client.login(username='author1', password='testpass123')
        
        # Search for "Blog" and filter by "published"
        response = self.client.get(f'{self.list_url}?search=Blog&status=published')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Blog Post')
        self.assertContains(response, 'Third Blog Post')
        self.assertNotContains(response, 'Second Blog Post')
    
    def test_blog_list_empty_state(self):
        """Test empty state when no posts exist."""
        # Delete all posts
        BlogPost.objects.all().delete()
        
        self.client.login(username='author1', password='testpass123')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No blog posts yet')
        self.assertContains(response, 'Create Your First Post')
    
    def test_blog_list_no_search_results(self):
        """Test empty state when search returns no results."""
        self.client.login(username='author1', password='testpass123')
        
        response = self.client.get(f'{self.list_url}?search=nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No posts found')
        self.assertContains(response, 'Clear Filters')
    
    def test_blog_list_context_data(self):
        """Test that proper context data is passed to template."""
        self.client.login(username='author1', password='testpass123')
        
        response = self.client.get(f'{self.list_url}?search=Blog&status=published')
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        self.assertEqual(response.context['title'], 'All Blog Posts')
        self.assertEqual(response.context['search_query'], 'Blog')
        self.assertEqual(response.context['status_filter'], 'published')
        self.assertIn('status_choices', response.context)
        self.assertIn('total_posts', response.context)
    
    def test_blog_list_ordering(self):
        """Test that posts are ordered by creation date (newest first)."""
        self.client.login(username='author1', password='testpass123')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        posts = response.context['blog_posts']
        
        # Posts should be ordered by created_at descending
        for i in range(len(posts) - 1):
            self.assertGreaterEqual(posts[i].created_at, posts[i + 1].created_at)
    
    def test_blog_list_select_related_optimization(self):
        """Test that the view uses select_related for performance."""
        self.client.login(username='author1', password='testpass123')
        
        # This test ensures that the queryset uses select_related('author')
        # to avoid N+1 queries when displaying author information
        with self.assertNumQueries(4):  # session, user, count (paginator), posts+authors
            response = self.client.get(self.list_url)
            
            # Access author information to trigger potential additional queries
            for post in response.context['blog_posts']:
                str(post.author.get_full_name())
    
    def test_blog_list_responsive_template(self):
        """Test that the template includes responsive design elements."""
        self.client.login(username='author1', password='testpass123')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for Bootstrap responsive classes
        self.assertContains(response, 'col-md-')
        self.assertContains(response, 'table-responsive')
        self.assertContains(response, 'btn-group-sm')
        
        # Check for mobile-friendly viewport meta tag in base template
        self.assertContains(response, 'viewport')
    
    def test_blog_list_navigation_links(self):
        """Test that navigation links are properly rendered."""
        self.client.login(username='author1', password='testpass123')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for navigation elements
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'All Posts')
        self.assertContains(response, 'active')  # Current page should be marked active
        
        # Check for action buttons (even if they're placeholder)
        self.assertContains(response, 'New Post')
        self.assertContains(response, 'View')
        self.assertContains(response, 'Edit')
        self.assertContains(response, 'Delete')


class BlogCreateViewTestCase(TestCase):
    """Test cases for blog create view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # URLs
        self.create_url = reverse('blog:create')
        self.list_url = reverse('blog:list')
        self.login_url = reverse('blog:admin_login')
    
    def test_blog_create_requires_authentication(self):
        """Test that blog create view requires authentication."""
        response = self.client.get(self.create_url)
        
        # Should redirect to login with next parameter
        expected_url = f'{self.login_url}?next={self.create_url}'
        self.assertRedirects(response, expected_url)
    
    def test_blog_create_form_display(self):
        """Test that blog create form displays correctly."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        
        # Check form fields are present
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="content"')
        self.assertContains(response, 'name="excerpt"')
        self.assertContains(response, 'name="status"')
        
        # Check form labels and help text
        self.assertContains(response, 'Title')
        self.assertContains(response, 'Content')
        self.assertContains(response, 'Status')
        self.assertContains(response, 'Markdown')
        
        # Check markdown toolbar
        self.assertContains(response, 'markdown-toolbar')
        self.assertContains(response, 'Preview')
    
    def test_blog_create_successful_submission(self):
        """Test successful blog post creation."""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'title': 'Test Blog Post',
            'content': 'This is test content for the blog post.',
            'excerpt': 'Test excerpt',
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, form_data)
        
        # Should redirect to blog list
        self.assertRedirects(response, self.list_url)
        
        # Blog post should be created
        self.assertTrue(BlogPost.objects.filter(title='Test Blog Post').exists())
        
        # Check blog post details
        blog_post = BlogPost.objects.get(title='Test Blog Post')
        self.assertEqual(blog_post.content, 'This is test content for the blog post.')
        self.assertEqual(blog_post.excerpt, 'Test excerpt')
        self.assertEqual(blog_post.status, 'draft')
        self.assertEqual(blog_post.author, self.user)
        self.assertEqual(blog_post.slug, 'test-blog-post')
    
    def test_blog_create_slug_generation(self):
        """Test automatic slug generation from title."""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'title': 'My Awesome Blog Post Title!',
            'content': 'Content here',
            'status': 'published'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertRedirects(response, self.list_url)
        
        blog_post = BlogPost.objects.get(title='My Awesome Blog Post Title!')
        self.assertEqual(blog_post.slug, 'my-awesome-blog-post-title')
    
    def test_blog_create_slug_uniqueness(self):
        """Test slug uniqueness handling."""
        # Create first blog post
        BlogPost.objects.create(
            title='Test Post',
            content='Content',
            status='published',
            author=self.user,
            slug='test-post'
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Try to create another post with same title
        form_data = {
            'title': 'Test Post',
            'content': 'Different content',
            'status': 'published'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertRedirects(response, self.list_url)
        
        # Second post should have unique slug
        new_post = BlogPost.objects.filter(title='Test Post').order_by('-created_at').first()
        self.assertEqual(new_post.slug, 'test-post-1')
    
    def test_blog_create_form_validation_errors(self):
        """Test form validation with invalid data."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with missing required fields
        form_data = {
            'title': '',
            'content': '',
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertEqual(response.status_code, 200)  # Should stay on form page
        
        # Should show validation errors
        self.assertContains(response, 'There were errors in your form')
        
        # No blog post should be created
        self.assertEqual(BlogPost.objects.count(), 0)
    
    def test_blog_create_title_validation(self):
        """Test title field validation."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with title too long
        long_title = 'x' * 201  # Exceeds 200 character limit
        form_data = {
            'title': long_title,
            'content': 'Valid content',
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertEqual(response.status_code, 200)
        
        # Should show validation error
        self.assertContains(response, 'There were errors in your form')
        self.assertEqual(BlogPost.objects.count(), 0)
    
    def test_blog_create_content_validation(self):
        """Test content field validation."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with content too short
        form_data = {
            'title': 'Valid Title',
            'content': 'short',  # Less than 10 characters
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertEqual(response.status_code, 200)
        
        # Should show validation error
        self.assertContains(response, 'There were errors in your form')
        self.assertEqual(BlogPost.objects.count(), 0)
    
    def test_blog_create_excerpt_validation(self):
        """Test excerpt field validation."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with excerpt too long
        long_excerpt = 'x' * 501  # Exceeds 500 character limit
        form_data = {
            'title': 'Valid Title',
            'content': 'Valid content that is long enough',
            'excerpt': long_excerpt,
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertEqual(response.status_code, 200)
        
        # Should show validation error
        self.assertContains(response, 'There were errors in your form')
        self.assertEqual(BlogPost.objects.count(), 0)
    
    def test_blog_create_optional_excerpt(self):
        """Test that excerpt field is optional."""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'title': 'Test Post',
            'content': 'Valid content that is long enough',
            'excerpt': '',  # Empty excerpt should be allowed
            'status': 'published'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertRedirects(response, self.list_url)
        
        # Blog post should be created with empty excerpt
        blog_post = BlogPost.objects.get(title='Test Post')
        self.assertEqual(blog_post.excerpt, '')
    
    def test_blog_create_status_choices(self):
        """Test that both draft and published status work."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test draft status
        form_data = {
            'title': 'Draft Post',
            'content': 'Content for draft post',
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertRedirects(response, self.list_url)
        
        draft_post = BlogPost.objects.get(title='Draft Post')
        self.assertEqual(draft_post.status, 'draft')
        
        # Test published status
        form_data = {
            'title': 'Published Post',
            'content': 'Content for published post',
            'status': 'published'
        }
        
        response = self.client.post(self.create_url, form_data)
        self.assertRedirects(response, self.list_url)
        
        published_post = BlogPost.objects.get(title='Published Post')
        self.assertEqual(published_post.status, 'published')
    
    def test_blog_create_success_message(self):
        """Test that success message is displayed after creation."""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'title': 'Success Test Post',
            'content': 'Content for success test',
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, form_data, follow=True)
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertTrue(any('created successfully' in str(m) for m in messages))
        self.assertTrue(any('Success Test Post' in str(m) for m in messages))
    
    def test_blog_create_context_data(self):
        """Test that proper context data is passed to template."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        self.assertEqual(response.context['title'], 'Create New Blog Post')
        self.assertEqual(response.context['submit_text'], 'Create Post')
        self.assertIn('cancel_url', response.context)
    
    def test_blog_create_cancel_functionality(self):
        """Test that cancel button links back to blog list."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for cancel link
        self.assertContains(response, f'href="{self.list_url}"')
        self.assertContains(response, 'Cancel')
        self.assertContains(response, 'Back to Posts')


class BlogDetailViewTestCase(TestCase):
    """Test cases for blog detail view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test blog posts
        self.post1 = BlogPost.objects.create(
            title='First Blog Post',
            content='# Heading\n\nThis is **bold** text and *italic* text.\n\n```python\nprint("Hello World")\n```',
            excerpt='First post excerpt',
            status='published',
            author=self.user,
            slug='first-blog-post'
        )
        
        self.post2 = BlogPost.objects.create(
            title='Second Blog Post',
            content='This is the second post content.',
            status='draft',
            author=self.user,
            slug='second-blog-post'
        )
        
        self.post3 = BlogPost.objects.create(
            title='Third Blog Post',
            content='This is the third post content.',
            status='published',
            author=self.user,
            slug='third-blog-post'
        )
        
        # URLs
        self.detail_url = reverse('blog:detail', kwargs={'slug': 'first-blog-post'})
        self.list_url = reverse('blog:list')
        self.login_url = reverse('blog:admin_login')
    
    def test_blog_detail_requires_authentication(self):
        """Test that blog detail view requires authentication."""
        response = self.client.get(self.detail_url)
        
        # Should redirect to login with next parameter
        expected_url = f'{self.login_url}?next={self.detail_url}'
        self.assertRedirects(response, expected_url)
    
    def test_blog_detail_displays_post(self):
        """Test that blog detail view displays post correctly."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check post information is displayed
        self.assertContains(response, 'First Blog Post')
        self.assertContains(response, 'first-blog-post')
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'Published')
        self.assertContains(response, 'First post excerpt')
    
    def test_blog_detail_markdown_rendering(self):
        """Test that markdown content is rendered correctly."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that markdown is rendered to HTML
        rendered_content = response.context['rendered_content']
        self.assertIn('<h1', rendered_content)  # H1 tag with possible attributes
        self.assertIn('Heading</h1>', rendered_content)
        self.assertIn('<strong>bold</strong>', rendered_content)
        self.assertIn('<em>italic</em>', rendered_content)
        self.assertIn('print(&quot;Hello World&quot;)', rendered_content)  # HTML encoded quotes
    
    def test_blog_detail_navigation_between_posts(self):
        """Test navigation between posts functionality."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test middle post (should have both previous and next)
        detail_url = reverse('blog:detail', kwargs={'slug': 'second-blog-post'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check navigation context
        self.assertIn('previous_post', response.context)
        self.assertIn('next_post', response.context)
        
        # Check navigation links are rendered
        self.assertContains(response, 'Previous Post')
        self.assertContains(response, 'Next Post')
    
    def test_blog_detail_no_navigation_for_single_post(self):
        """Test navigation when there's only one post."""
        # Delete other posts to test single post scenario
        BlogPost.objects.exclude(slug='first-blog-post').delete()
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Should show no navigation
        self.assertIsNone(response.context['previous_post'])
        self.assertIsNone(response.context['next_post'])
    
    def test_blog_detail_preview_markdown_toggle(self):
        """Test that preview/markdown toggle functionality is present."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for toggle buttons
        self.assertContains(response, 'id="preview-btn"')
        self.assertContains(response, 'id="markdown-btn"')
        self.assertContains(response, 'showPreview()')
        self.assertContains(response, 'showMarkdown()')
        
        # Check for both content containers
        self.assertContains(response, 'id="content-preview"')
        self.assertContains(response, 'id="content-markdown"')
    
    def test_blog_detail_context_data(self):
        """Test that proper context data is passed to template."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        self.assertEqual(response.context['title'], 'Preview: First Blog Post')
        self.assertIn('rendered_content', response.context)
        self.assertIn('list_url', response.context)
        self.assertEqual(response.context['blog_post'], self.post1)
    
    def test_blog_detail_select_related_optimization(self):
        """Test that the view uses select_related for performance."""
        self.client.login(username='testuser', password='testpass123')
        
        # This test ensures that the queryset uses select_related('author')
        with self.assertNumQueries(5):  # session, user, post+author, previous post, next post
            response = self.client.get(self.detail_url)
            
            # Access author information to ensure no additional queries
            str(response.context['blog_post'].author.get_full_name())
    
    def test_blog_detail_404_for_nonexistent_post(self):
        """Test that 404 is returned for non-existent post."""
        self.client.login(username='testuser', password='testpass123')
        
        nonexistent_url = reverse('blog:detail', kwargs={'slug': 'nonexistent-post'})
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, 404)
    
    def test_blog_detail_action_buttons(self):
        """Test that action buttons are present."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for action buttons
        self.assertContains(response, 'Back to All Posts')
        self.assertContains(response, 'Edit Post')
        self.assertContains(response, 'Delete Post')
        self.assertContains(response, 'Back to Posts')
    
    def test_blog_detail_responsive_design(self):
        """Test that the template includes responsive design elements."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for Bootstrap responsive classes
        self.assertContains(response, 'col-md-')
        self.assertContains(response, 'btn-group-sm')
        self.assertContains(response, 'd-flex')
        
        # Check for mobile-friendly elements
        self.assertContains(response, 'justify-content-md-end')
        self.assertContains(response, 'order-md-')
    
    def test_blog_detail_post_meta_information(self):
        """Test that post meta information is displayed correctly."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for meta information
        self.assertContains(response, 'Post Information')
        self.assertContains(response, 'Title:')
        self.assertContains(response, 'Slug:')
        self.assertContains(response, 'Status:')
        self.assertContains(response, 'Author:')
        self.assertContains(response, 'Created:')
        self.assertContains(response, 'Updated:')
        
        # Check for excerpt if present
        self.assertContains(response, 'Excerpt:')
    
    def test_blog_detail_navigation_links_work(self):
        """Test that navigation links between posts work correctly."""
        self.client.login(username='testuser', password='testpass123')
        
        # Get the second post detail page
        detail_url = reverse('blog:detail', kwargs={'slug': 'second-blog-post'})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that navigation links are present and correct
        previous_post = response.context['previous_post']
        next_post = response.context['next_post']
        
        if previous_post:
            prev_url = reverse('blog:detail', kwargs={'slug': previous_post.slug})
            self.assertContains(response, prev_url)
        
        if next_post:
            next_url = reverse('blog:detail', kwargs={'slug': next_post.slug})
            self.assertContains(response, next_url)


class BlogUpdateViewTestCase(TestCase):
    """Test cases for blog update view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.username = 'testuser'
        self.password = 'testpass123'
        self.email = 'test@example.com'
        
        # Create test user
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            is_active=True
        )
        
        # Create another user for authorization tests
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            is_active=True
        )
        
        # Create test blog posts
        self.blog_post = BlogPost.objects.create(
            title='Test Blog Post',
            slug='test-blog-post',
            content='This is test content for the blog post.',
            excerpt='Test excerpt',
            status='draft',
            author=self.user
        )
        
        self.published_post = BlogPost.objects.create(
            title='Published Blog Post',
            slug='published-blog-post',
            content='This is published content.',
            excerpt='Published excerpt',
            status='published',
            author=self.user
        )
        
        # URLs
        self.update_url = reverse('blog:update', kwargs={'slug': self.blog_post.slug})
        self.published_update_url = reverse('blog:update', kwargs={'slug': self.published_post.slug})
        self.login_url = reverse('blog:admin_login')
    
    def test_update_view_requires_authentication(self):
        """Test that update view requires user authentication."""
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'{self.login_url}?next={self.update_url}')
    
    def test_update_view_loads_with_authentication(self):
        """Test that update view loads correctly for authenticated users."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Blog Post')
        self.assertContains(response, self.blog_post.title)
    
    def test_update_view_form_pre_population(self):
        """Test that update form is pre-populated with existing data."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that form fields are pre-populated
        form = response.context['form']
        self.assertEqual(form.initial.get('title') or form.instance.title, self.blog_post.title)
        self.assertEqual(form.initial.get('content') or form.instance.content, self.blog_post.content)
        self.assertEqual(form.initial.get('excerpt') or form.instance.excerpt, self.blog_post.excerpt)
        self.assertEqual(form.initial.get('status') or form.instance.status, self.blog_post.status)
        
        # Check that form fields contain the values in HTML
        self.assertContains(response, self.blog_post.title)
        self.assertContains(response, self.blog_post.content)
        self.assertContains(response, self.blog_post.excerpt)
    
    def test_update_view_context_data(self):
        """Test that update view provides correct context data."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        self.assertIn('blog_post', response.context)
        self.assertIn('title', response.context)
        self.assertIn('submit_text', response.context)
        self.assertIn('cancel_url', response.context)
        self.assertIn('list_url', response.context)
        
        # Check context values
        self.assertEqual(response.context['blog_post'], self.blog_post)
        self.assertEqual(response.context['title'], f'Edit: {self.blog_post.title}')
        self.assertEqual(response.context['submit_text'], 'Update Post')
        
        # Check URLs
        expected_cancel_url = reverse('blog:detail', kwargs={'slug': self.blog_post.slug})
        expected_list_url = reverse('blog:list')
        self.assertEqual(response.context['cancel_url'], expected_cancel_url)
        self.assertEqual(response.context['list_url'], expected_list_url)
    
    def test_successful_blog_post_update(self):
        """Test successful blog post update with valid data."""
        self.client.login(username=self.username, password=self.password)
        
        # Store original timestamps
        original_created_at = self.blog_post.created_at
        original_updated_at = self.blog_post.updated_at
        
        # Update data
        updated_data = {
            'title': 'Updated Test Blog Post',
            'content': 'This is updated content for the blog post.',
            'excerpt': 'Updated excerpt',
            'status': 'published'
        }
        
        response = self.client.post(self.update_url, updated_data)
        
        # Check redirect to detail view
        expected_redirect_url = reverse('blog:detail', kwargs={'slug': 'updated-test-blog-post'})
        self.assertRedirects(response, expected_redirect_url)
        
        # Refresh from database
        self.blog_post.refresh_from_db()
        
        # Check that data was updated
        self.assertEqual(self.blog_post.title, 'Updated Test Blog Post')
        self.assertEqual(self.blog_post.content, 'This is updated content for the blog post.')
        self.assertEqual(self.blog_post.excerpt, 'Updated excerpt')
        self.assertEqual(self.blog_post.status, 'published')
        
        # Check that slug was updated
        self.assertEqual(self.blog_post.slug, 'updated-test-blog-post')
        
        # Check timestamp handling
        self.assertEqual(self.blog_post.created_at, original_created_at)  # Should preserve creation date
        self.assertGreater(self.blog_post.updated_at, original_updated_at)  # Should update modification date
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('updated successfully' in str(message) for message in messages))
    
    def test_update_preserves_creation_date(self):
        """Test that updating a blog post preserves the original creation date."""
        self.client.login(username=self.username, password=self.password)
        
        original_created_at = self.blog_post.created_at
        
        updated_data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'excerpt': 'Updated excerpt',
            'status': 'published'
        }
        
        self.client.post(self.update_url, updated_data)
        
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.created_at, original_created_at)
    
    def test_update_timestamp_handling(self):
        """Test that update timestamp is automatically updated."""
        self.client.login(username=self.username, password=self.password)
        
        original_updated_at = self.blog_post.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        updated_data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'excerpt': 'Updated excerpt',
            'status': 'draft'
        }
        
        self.client.post(self.update_url, updated_data)
        
        self.blog_post.refresh_from_db()
        self.assertGreater(self.blog_post.updated_at, original_updated_at)
    
    def test_update_with_invalid_data(self):
        """Test blog post update with invalid data."""
        self.client.login(username=self.username, password=self.password)
        
        # Test with empty title
        invalid_data = {
            'title': '',
            'content': 'Some content',
            'excerpt': 'Some excerpt',
            'status': 'draft'
        }
        
        response = self.client.post(self.update_url, invalid_data)
        self.assertEqual(response.status_code, 200)  # Should return form with errors
        self.assertContains(response, 'There were errors in your form')
        
        # Check that blog post was not updated
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.title, 'Test Blog Post')  # Original title
    
    def test_update_with_empty_content(self):
        """Test blog post update with empty content."""
        self.client.login(username=self.username, password=self.password)
        
        invalid_data = {
            'title': 'Valid Title',
            'content': '',
            'excerpt': 'Some excerpt',
            'status': 'draft'
        }
        
        response = self.client.post(self.update_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'There were errors in your form')
        
        # Check that blog post was not updated
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.content, 'This is test content for the blog post.')
    
    def test_update_with_duplicate_title(self):
        """Test blog post update with title that would create duplicate slug."""
        self.client.login(username=self.username, password=self.password)
        
        # Try to update with the title of the published post
        duplicate_data = {
            'title': 'Published Blog Post',  # This already exists
            'content': 'Updated content',
            'excerpt': 'Updated excerpt',
            'status': 'draft'
        }
        
        response = self.client.post(self.update_url, duplicate_data)
        
        # Should handle duplicate by creating unique slug
        if response.status_code == 302:  # Successful update with unique slug
            self.blog_post.refresh_from_db()
            self.assertEqual(self.blog_post.title, 'Published Blog Post')
            self.assertNotEqual(self.blog_post.slug, 'published-blog-post')  # Should be different
            self.assertTrue(self.blog_post.slug.startswith('published-blog-post-'))
        else:  # Form validation error
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'similar title already exists')
    
    def test_update_nonexistent_post(self):
        """Test updating a non-existent blog post."""
        self.client.login(username=self.username, password=self.password)
        
        nonexistent_url = reverse('blog:update', kwargs={'slug': 'nonexistent-post'})
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, 404)
    
    def test_update_view_template_elements(self):
        """Test that update view template contains required elements."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        
        # Check for form elements
        self.assertContains(response, 'form method="post"')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="content"')
        self.assertContains(response, 'name="excerpt"')
        self.assertContains(response, 'name="status"')
        
        # Check for buttons and links
        self.assertContains(response, 'Update Post')  # Submit button
        self.assertContains(response, 'Cancel')  # Cancel button
        self.assertContains(response, 'Back to Post')  # Back to detail link
        self.assertContains(response, 'All Posts')  # Back to list link
        
        # Check for markdown editor elements
        self.assertContains(response, 'markdown-editor')
        self.assertContains(response, 'markdown-toolbar')
        self.assertContains(response, 'Preview')
        
        # Check for post information
        self.assertContains(response, 'Created:')
        self.assertContains(response, 'Last updated:')
        self.assertContains(response, self.blog_post.get_status_display())
    
    def test_cancel_functionality(self):
        """Test that cancel button redirects without saving changes."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that cancel URL is correct
        expected_cancel_url = reverse('blog:detail', kwargs={'slug': self.blog_post.slug})
        self.assertContains(response, f'href="{expected_cancel_url}"')
        
        # Test that following cancel link doesn't change the post
        original_title = self.blog_post.title
        cancel_response = self.client.get(expected_cancel_url)
        self.assertEqual(cancel_response.status_code, 200)
        
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.title, original_title)  # Should be unchanged
    
    def test_update_view_navigation_links(self):
        """Test that navigation links in update view work correctly."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        
        # Check navigation URLs
        detail_url = reverse('blog:detail', kwargs={'slug': self.blog_post.slug})
        list_url = reverse('blog:list')
        
        self.assertContains(response, detail_url)
        self.assertContains(response, list_url)
    
    def test_update_form_validation_messages(self):
        """Test that form validation messages are displayed correctly."""
        self.client.login(username=self.username, password=self.password)
        
        # Submit form with validation errors
        invalid_data = {
            'title': '',  # Required field
            'content': 'x',  # Too short
            'excerpt': 'x' * 600,  # Too long
            'status': 'invalid_status'  # Invalid choice
        }
        
        response = self.client.post(self.update_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        
        # Check for error messages
        self.assertContains(response, 'There were errors in your form')
        
        # Check that form shows validation errors
        form = response.context['form']
        self.assertTrue(form.errors)
    
    def test_update_success_message(self):
        """Test that success message is displayed after successful update."""
        self.client.login(username=self.username, password=self.password)
        
        updated_data = {
            'title': 'Successfully Updated Post',
            'content': 'This content was successfully updated.',
            'excerpt': 'Updated excerpt',
            'status': 'published'
        }
        
        response = self.client.post(self.update_url, updated_data, follow=True)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        success_messages = [msg for msg in messages if 'updated successfully' in str(msg)]
        self.assertTrue(success_messages)
        self.assertIn('Successfully Updated Post', str(success_messages[0]))
    
    def test_update_view_preserves_author(self):
        """Test that updating a post preserves the original author."""
        self.client.login(username=self.username, password=self.password)
        
        original_author = self.blog_post.author
        
        updated_data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'excerpt': 'Updated excerpt',
            'status': 'published'
        }
        
        self.client.post(self.update_url, updated_data)
        
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.author, original_author)
    
    def test_update_view_slug_generation(self):
        """Test that slug is properly updated when title changes."""
        self.client.login(username=self.username, password=self.password)
        
        updated_data = {
            'title': 'Completely New Title',
            'content': 'Updated content',
            'excerpt': 'Updated excerpt',
            'status': 'draft'
        }
        
        response = self.client.post(self.update_url, updated_data)
        
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.slug, 'completely-new-title')
        
        # Check redirect uses new slug
        expected_redirect_url = reverse('blog:detail', kwargs={'slug': 'completely-new-title'})
        self.assertRedirects(response, expected_redirect_url)