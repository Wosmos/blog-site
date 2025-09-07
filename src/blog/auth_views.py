from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from functools import wraps


@csrf_protect
@never_cache
def blog_admin_login(request):
    """
    Custom login view for blog admin interface.
    Handles authentication and redirects to blog admin dashboard.
    """
    if request.user.is_authenticated:
        return redirect('blog:admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    
                    # Redirect to next URL or default to admin dashboard
                    next_url = request.GET.get('next', reverse('blog:admin_dashboard'))
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account has been disabled.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return render(request, 'blog/auth/login.html', {
        'title': 'Blog Admin Login'
    })


@login_required
def blog_admin_logout(request):
    """
    Custom logout view for blog admin interface.
    Logs out user and redirects to login page with confirmation message.
    """
    username = request.user.username
    logout(request)
    messages.success(request, f'You have been successfully logged out, {username}.')
    return redirect('blog:admin_login')


def admin_required(view_func):
    """
    Decorator that requires user to be authenticated and active.
    Redirects to login page if not authenticated.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access the blog admin interface.')
            return redirect(f"{reverse('blog:admin_login')}?next={request.path}")
        
        if not request.user.is_active:
            messages.error(request, 'Your account has been disabled. Please contact an administrator.')
            return redirect('blog:admin_login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def staff_required(view_func):
    """
    Decorator that requires user to be authenticated and staff member.
    More restrictive than admin_required for sensitive operations.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this feature.')
            return redirect(f"{reverse('blog:admin_login')}?next={request.path}")
        
        if not request.user.is_active:
            messages.error(request, 'Your account has been disabled.')
            return redirect('blog:admin_login')
        
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this feature.')
            return redirect('blog:admin_dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper