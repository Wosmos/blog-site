import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import BlogPost


class Command(BaseCommand):
    help = "Seed database with a super_admin user and sample blog posts"

    def handle(self, *args, **options):
        User = get_user_model()

        # Create or get super_admin user
        username = "super_admin"
        email = "super_admin@example.com"
        password = "admin123"  # development-only password

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Created superuser '{username}' with password '{password}' (dev only, change in production)."
            ))
        else:
            # Ensure flags are set in case this user already existed
            updated = False
            if not user.is_staff:
                user.is_staff = True
                updated = True
            if not user.is_superuser:
                user.is_superuser = True
                updated = True
            if updated:
                user.save()
            self.stdout.write(self.style.WARNING(
                f"Superuser '{username}' already exists. Password unchanged."
            ))

        # Delete all existing blog posts
        deleted_count = BlogPost.objects.all().count()
        BlogPost.objects.all().delete()
        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(
                f"Deleted {deleted_count} existing blog posts."
            ))

        # Define blog posts with shorter, safe content snippets
        blog_posts = [
            {
                "title": "Mastering Django ORM: A Complete Guide to Database Queries",
                "excerpt": "Learn how to leverage Django's powerful ORM to write efficient database queries and avoid common pitfalls.",
                "status": "published",
                "content": (
                    "# Mastering Django ORM\n\n"
                    "Django's ORM lets you work with your database using Python objects instead of raw SQL. "
                    "This post introduces basic queries, filtering, and best practices such as using "
                    "`select_related`, `prefetch_related`, and pagination for large datasets."
                ),
            },
            {
                "title": "Building RESTful APIs with Django REST Framework: Best Practices",
                "excerpt": "A practical overview of creating robust REST APIs using Django REST Framework.",
                "status": "published",
                "content": (
                    "# Building RESTful APIs with DRF\n\n"
                    "Django REST Framework (DRF) makes it easy to build clean, well-structured APIs. "
                    "You define serializers, viewsets, and routers, and DRF handles the rest, including "
                    "authentication, permissions, and pagination."
                ),

### 1. Define Serializers

```python
from rest_framework import serializers
from .models import BlogPost

class BlogPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'content', 'author', 'author_name', 'created_at']
        read_only_fields = ['author', 'created_at']
```

### 2. Create Views

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

### 3. Configure URLs

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'posts', BlogPostViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

## Advanced Features

### Custom Actions

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class BlogPostViewSet(viewsets.ModelViewSet):
    # ... existing code ...
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        post = self.get_object()
        post.status = 'published'
        post.save()
        return Response({'status': 'post published'})
```

### Filtering and Search

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'author']
    search_fields = ['title', 'content']
```

## Authentication Strategies

### Token Authentication

```python
# Generate tokens
from rest_framework.authtoken.models import Token

token = Token.objects.create(user=user)
print(token.key)

# Use in requests
headers = {'Authorization': f'Token {token.key}'}
```

### JWT Authentication

```bash
pip install djangorestframework-simplejwt
```

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

## Testing Your API

```python
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

class BlogPostAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_post(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Test Post',
            'content': 'Test content'
        }
        response = self.client.post('/api/posts/', data)
        self.assertEqual(response.status_code, 201)
```

## Performance Tips

1. **Use pagination** for list endpoints
2. **Implement caching** for frequently accessed data
3. **Optimize serializers** with `select_related()` and `prefetch_related()`
4. **Use throttling** to prevent abuse
5. **Enable compression** for large responses

## Conclusion

Django REST Framework provides everything you need to build production-ready APIs. Start simple, then leverage advanced features as your needs grow.

**Next Steps**: Explore API versioning, webhooks, and real-time features with Django Channels!
"""
            },
            {
                "title": "Django Security Best Practices: Protecting Your Web Application",
                "excerpt": "Essential security measures every Django developer should implement. From CSRF protection to secure deployment, learn how to keep your application safe.",
                "status": "published",
                "content": """# Django Security Best Practices

Security should never be an afterthought. Django provides excellent security features out of the box, but you need to know how to use them properly.

## Built-in Security Features

Django comes with several security features enabled by default:

- **CSRF Protection**: Prevents Cross-Site Request Forgery attacks
- **SQL Injection Protection**: ORM automatically escapes queries
- **XSS Protection**: Template system auto-escapes variables
- **Clickjacking Protection**: X-Frame-Options header
- **SSL/HTTPS**: Enforced with middleware

## Essential Security Settings

### 1. Secret Key Management

**❌ Never do this:**

```python
SECRET_KEY = 'django-insecure-hardcoded-key-123'
```

**✅ Do this instead:**

```python
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")
```

### 2. Debug Mode

```python
# settings.py
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Never use DEBUG=True in production!
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
```

### 3. Database Security

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

## HTTPS and SSL

### Force HTTPS in Production

```python
# settings.py
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

## Authentication Best Practices

### 1. Strong Password Requirements

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### 2. Implement Rate Limiting

```python
# Using django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # Login logic here
    pass
```

### 3. Two-Factor Authentication

```bash
pip install django-two-factor-auth
```

## Protecting Against Common Attacks

### XSS Prevention

```html
<!-- Django templates auto-escape by default -->
{{ user_input }}  <!-- Safe -->

<!-- Only use 'safe' when you trust the content -->
{{ trusted_html|safe }}

<!-- Or use mark_safe in views -->
from django.utils.safestring import mark_safe
```

### SQL Injection Prevention

```python
# ❌ Never do this
User.objects.raw(f"SELECT * FROM users WHERE username = '{username}'")

# ✅ Always use parameterized queries
User.objects.raw("SELECT * FROM users WHERE username = %s", [username])

# ✅ Or better, use the ORM
User.objects.filter(username=username)
```

### CSRF Protection

```html
<!-- Always include CSRF token in forms -->
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

```python
# For AJAX requests
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

@ensure_csrf_cookie
def my_view(request):
    # View logic
    pass
```

## File Upload Security

```python
# models.py
from django.core.validators import FileExtensionValidator

class Document(models.Model):
    file = models.FileField(
        upload_to='documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
```

```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# Serve media files securely
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

## Security Headers

```python
# settings.py
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Add security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware
]
```

## Logging and Monitoring

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/security.log'),
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

## Security Checklist

Before deploying to production:

- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS and security headers
- [ ] Implement strong password policies
- [ ] Set up rate limiting
- [ ] Configure proper file upload validation
- [ ] Enable logging and monitoring
- [ ] Run `python manage.py check --deploy`
- [ ] Keep Django and dependencies updated

## Conclusion

Security is an ongoing process, not a one-time task. Stay informed about new vulnerabilities, keep your dependencies updated, and regularly audit your code.

**Remember**: The most secure code is the code that doesn't exist. Keep your application simple and avoid unnecessary complexity.
"""
            },
            {
                "title": "Async Django: Building High-Performance Applications with ASGI",
                "excerpt": "Unlock the power of asynchronous programming in Django. Learn how to handle thousands of concurrent connections and build real-time features.",
                "status": "published",
                "content": """# Async Django: Building High-Performance Applications

Django 3.1+ introduced native support for asynchronous views and middleware, opening up new possibilities for building high-performance, real-time applications.

## Why Async?

Traditional synchronous code blocks while waiting for I/O operations:

```python
# Synchronous - blocks for 5 seconds total
def sync_view(request):
    result1 = slow_api_call()  # 2 seconds
    result2 = another_api_call()  # 3 seconds
    return HttpResponse(f"{result1} {result2}")
```

Async code can handle multiple operations concurrently:

```python
# Asynchronous - completes in ~3 seconds
async def async_view(request):
    result1, result2 = await asyncio.gather(
        slow_api_call(),  # 2 seconds
        another_api_call()  # 3 seconds (runs concurrently)
    )
    return HttpResponse(f"{result1} {result2}")
```

## Setting Up ASGI

### 1. Install ASGI Server

```bash
pip install uvicorn gunicorn
```

### 2. Configure ASGI Application

```python
# asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_asgi_application()
```

### 3. Run with Uvicorn

```bash
uvicorn myproject.asgi:application --reload
```

## Async Views

### Basic Async View

```python
from django.http import JsonResponse
import httpx
import asyncio

async def async_weather_view(request):
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.weather.com/current')
        data = response.json()
    return JsonResponse(data)
```

### Multiple Concurrent Requests

```python
async def dashboard_view(request):
    async with httpx.AsyncClient() as client:
        # All requests run concurrently
        weather, news, stocks = await asyncio.gather(
            client.get('https://api.weather.com/current'),
            client.get('https://api.news.com/latest'),
            client.get('https://api.stocks.com/prices'),
        )
    
    return JsonResponse({
        'weather': weather.json(),
        'news': news.json(),
        'stocks': stocks.json(),
    })
```

## Async Database Queries

Django 4.1+ supports async database operations:

```python
from django.http import JsonResponse
from .models import BlogPost

async def async_posts_view(request):
    # Async ORM query
    posts = [post async for post in BlogPost.objects.filter(status='published')]
    
    return JsonResponse({
        'posts': [
            {'title': post.title, 'excerpt': post.excerpt}
            for post in posts
        ]
    })
```

### Async Query Operations

```python
# Async get
post = await BlogPost.objects.aget(pk=1)

# Async filter
posts = [p async for p in BlogPost.objects.filter(status='published')]

# Async create
post = await BlogPost.objects.acreate(
    title='Async Post',
    content='Created asynchronously'
)

# Async update
post.title = 'Updated Title'
await post.asave()

# Async delete
await post.adelete()
```

## Async Middleware

```python
# middleware.py
import time

class AsyncTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        start_time = time.time()
        
        response = await self.get_response(request)
        
        duration = time.time() - start_time
        response['X-Response-Time'] = str(duration)
        
        return response
```

## WebSockets with Django Channels

For real-time features, use Django Channels:

```bash
pip install channels
```

```python
# settings.py
INSTALLED_APPS = [
    'channels',
    # ...
]

ASGI_APPLICATION = 'myproject.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],
        },
    },
}
```

### WebSocket Consumer

```python
# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))
```

## Performance Considerations

### When to Use Async

**✅ Good use cases:**
- External API calls
- Multiple concurrent I/O operations
- WebSocket connections
- Long-polling
- Server-Sent Events

**❌ Not beneficial for:**
- CPU-intensive tasks
- Simple database queries
- File processing
- When your entire stack isn't async

### Mixing Sync and Async

```python
from asgiref.sync import sync_to_async

# Call sync function from async context
@sync_to_async
def sync_heavy_computation():
    # CPU-intensive work
    return result

async def async_view(request):
    result = await sync_heavy_computation()
    return JsonResponse({'result': result})
```

## Testing Async Views

```python
from django.test import AsyncClient, TestCase

class AsyncViewTests(TestCase):
    async def test_async_view(self):
        client = AsyncClient()
        response = await client.get('/async-endpoint/')
        self.assertEqual(response.status_code, 200)
```

## Production Deployment

### Using Uvicorn + Gunicorn

```bash
gunicorn myproject.asgi:application -k uvicorn.workers.UvicornWorker
```

### Docker Configuration

```dockerfile
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "myproject.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

## Conclusion

Async Django opens up exciting possibilities for building high-performance applications. Start by identifying I/O-bound operations in your application and gradually migrate them to async.

**Pro tip**: Don't async everything. Profile your application and optimize where it matters most!
"""
            },
            {
                "title": "Django Testing: A Comprehensive Guide to Writing Better Tests",
                "excerpt": "Master the art of testing Django applications. From unit tests to integration tests, learn how to write maintainable, reliable test suites.",
                "status": "published",
                "content": """# Django Testing: Writing Better Tests

Good tests are the foundation of maintainable software. Let's explore how to write comprehensive tests for your Django applications.

## Types of Tests

### Unit Tests
Test individual components in isolation.

### Integration Tests
Test how components work together.

### Functional Tests
Test complete user workflows.

## Basic Test Structure

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import BlogPost

class BlogPostModelTest(TestCase):
    def setUp(self):
        """Run before each test method"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = BlogPost.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user
        )
    
    def test_post_creation(self):
        """Test that post is created correctly"""
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.author, self.user)
    
    def tearDown(self):
        """Run after each test method"""
        # Cleanup if needed
        pass
```

## Testing Models

```python
class BlogPostModelTest(TestCase):
    def test_string_representation(self):
        post = BlogPost(title="Test Title")
        self.assertEqual(str(post), "Test Title")
    
    def test_slug_generation(self):
        post = BlogPost.objects.create(
            title="Test Post Title",
            author=self.user
        )
        self.assertEqual(post.slug, "test-post-title")
    
    def test_published_manager(self):
        BlogPost.objects.create(
            title="Published",
            author=self.user,
            status='published'
        )
        BlogPost.objects.create(
            title="Draft",
            author=self.user,
            status='draft'
        )
        
        published = BlogPost.published.all()
        self.assertEqual(published.count(), 1)
```

## Testing Views

```python
from django.test import TestCase, Client
from django.urls import reverse

class BlogPostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = BlogPost.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            status='published'
        )
    
    def test_list_view(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertTemplateUsed(response, 'blog/post_list.html')
    
    def test_detail_view(self):
        url = reverse('blog:post_detail', kwargs={'pk': self.post.pk})
            },
        ]

        # Create BlogPost instances from the blog_posts definitions
        created_count = 0
        skipped_count = 0

        for index, data in enumerate(blog_posts, start=1):
            post, created = BlogPost.objects.get_or_create(
                title=data["title"],
                author=user,
                defaults={
                    "content": data["content"],
                    "excerpt": data["excerpt"],
                    "status": data["status"],
                },
            )

            if created:
                created_count += 1

                # Optionally spread timestamps over the last 10 days
                days_ago = random.randint(0, 10)
                timestamp = timezone.now() - timedelta(days=days_ago)
                BlogPost.objects.filter(pk=post.pk).update(
                    created_at=timestamp,
                    updated_at=timestamp,
                )

                self.stdout.write(self.style.SUCCESS(
                    f"Created blog post: '{post.title}' ({post.status})"
                ))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(
                    f"Blog post already exists, skipped: '{post.title}'"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete. Created {created_count} posts, skipped {skipped_count} existing posts."
        ))
