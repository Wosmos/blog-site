from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from functools import wraps
import secrets
import string
from datetime import timedelta
from django.utils import timezone
from .auth_forms import (
    CustomUserCreationForm, 
    TwoFactorSetupForm, 
    TwoFactorForm, 
    ForgotPasswordForm, 
    ResetPasswordForm
)
from .models import UserProfile, PasswordResetToken


@csrf_protect
@never_cache
def register(request):
    """
    User registration view with email verification.
    """
    if request.user.is_authenticated:
        return redirect('blog:admin_dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Generate email verification token
            verification_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(50))
            user.profile.email_verification_token = verification_token
            user.profile.save()

            # Send verification email
            verification_link = request.build_absolute_uri(
                reverse('blog:verify_email', kwargs={'token': verification_token})
            )

            subject = 'Verify Your Email Address'
            html_message = render_to_string('blog/auth/verification_email.html', {
                'user': user,
                'verification_link': verification_link,
            })
            plain_message = strip_tags(html_message)

            try:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message
                )
                messages.success(request, 'Registration successful! Please check your email to verify your account.')
            except Exception as e:
                # If email fails, still allow login but mark as unverified
                messages.warning(request, 'Registration successful, but verification email could not be sent. Please contact support.')

            return redirect('blog:admin_login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'blog/auth/register.html', {
        'title': 'Register',
        'form': form
    })


def verify_email(request, token):
    """
    Verify user email using token.
    """
    try:
        user_profile = UserProfile.objects.get(email_verification_token=token)
        user_profile.email_verified = True
        user_profile.email_verification_token = None
        user_profile.save()

        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('blog:admin_login')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
        return redirect('blog:admin_login')


@login_required
def setup_2fa(request):
    """
    Setup 2FA for the user.
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = TwoFactorSetupForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']

            # Verify the code with the user's OTP secret
            if profile.verify_otp(verification_code):
                profile.is_2fa_enabled = True
                profile.save()
                messages.success(request, '2FA has been enabled successfully!')
                return redirect('blog:admin_dashboard')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        # Generate a new OTP secret if one doesn't exist
        if not profile.otp_secret:
            profile.generate_otp_secret()
            profile.save()

        # Generate QR code for authenticator app
        qr_uri = profile.get_totp_uri()

        form = TwoFactorSetupForm()

    return render(request, 'blog/auth/setup_2fa.html', {
        'title': 'Setup Two-Factor Authentication',
        'qr_uri': qr_uri,
        'form': form
    })


@login_required
def disable_2fa(request):
    """
    Disable 2FA for the user.
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile.is_2fa_enabled = False
    profile.otp_secret = None
    profile.save()
    messages.success(request, '2FA has been disabled successfully!')
    return redirect('blog:admin_dashboard')


def verify_2fa(request, user_id=None):
    """
    Verify 2FA token after login.
    """
    if request.user.is_authenticated:
        return redirect('blog:admin_dashboard')

    if request.method == 'POST':
        form = TwoFactorForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']

            # Get user from session (stored after initial login)
            user_id = request.session.get('user_id_for_2fa_verification')
            if not user_id:
                messages.error(request, 'Session expired. Please log in again.')
                return redirect('blog:admin_login')

            try:
                user = User.objects.get(id=user_id)
                profile, created = UserProfile.objects.get_or_create(user=user)

                if profile.verify_otp(token):
                    # 2FA verification successful, log in the user
                    from django.contrib.auth import login
                    login(request, user)

                    # Clear the session data
                    if 'user_id_for_2fa_verification' in request.session:
                        del request.session['user_id_for_2fa_verification']

                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    next_url = request.GET.get('next', reverse('blog:admin_dashboard'))
                    return redirect(next_url)
                else:
                    form.add_error('token', 'Invalid verification code. Please try again.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('blog:admin_login')
    else:
        form = TwoFactorForm()

    return render(request, 'blog/auth/verify_2fa.html', {
        'title': 'Verify Two-Factor Authentication',
        'form': form
    })


def forgot_password(request):
    """
    Handle password reset request.
    """
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)

                # Generate password reset token

                token = secrets.token_urlsafe(50)

                # Create or update password reset token
                reset_token, created = PasswordResetToken.objects.get_or_create(
                    user=user,
                    defaults={
                        'token': token,
                        'expires_at': timezone.now() + timedelta(hours=24)
                    }
                )

                if not created:
                    # Update the existing token
                    reset_token.token = token
                    reset_token.expires_at = timezone.now() + timedelta(hours=24)
                    reset_token.used = False
                    reset_token.save()

                # Send password reset email
                reset_link = request.build_absolute_uri(
                    reverse('blog:reset_password', kwargs={'token': reset_token.token})
                )

                subject = 'Password Reset Request'
                html_message = render_to_string('blog/auth/password_reset_email.html', {
                    'user': user,
                    'reset_link': reset_link,
                })
                plain_message = strip_tags(html_message)

                try:
                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=html_message
                    )
                    messages.success(request, 'Password reset link has been sent to your email address.')
                except Exception as e:
                    messages.error(request, 'There was an error sending the password reset email. Please try again later.')

                return redirect('blog:admin_login')
            except User.DoesNotExist:
                # Don't reveal that the email doesn't exist for security
                messages.success(request, 'If an account with that email exists, a password reset link has been sent.')
                return redirect('blog:admin_login')
    else:
        form = ForgotPasswordForm()

    return render(request, 'blog/auth/forgot_password.html', {
        'title': 'Forgot Password',
        'form': form
    })


def reset_password(request, token):
    """
    Handle password reset with token.
    """
    try:
        reset_token = PasswordResetToken.objects.get(token=token)

        # Check if token is expired
        if reset_token.expires_at < timezone.now():
            messages.error(request, 'This password reset link has expired. Please request a new one.')
            return redirect('blog:admin_login')

        # Check if token has been used
        if reset_token.used:
            messages.error(request, 'This password reset link has already been used. Please request a new one.')
            return redirect('blog:admin_login')

        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                # Set the new password
                user = reset_token.user
                user.set_password(form.cleaned_data['password1'])
                user.save()

                # Mark the token as used
                reset_token.used = True
                reset_token.save()

                messages.success(request, 'Your password has been reset successfully! You can now log in with your new password.')
                return redirect('blog:admin_login')
        else:
            form = ResetPasswordForm()

        return render(request, 'blog/auth/reset_password.html', {
            'title': 'Reset Password',
            'form': form,
            'token': token
        })
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('blog:admin_login')


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
                    # Check if user has 2FA enabled
                    if hasattr(user, 'profile') and user.profile.is_2fa_enabled:
                        # Store user ID in session for 2FA verification
                        request.session['user_id_for_2fa_verification'] = user.id
                        return redirect('blog:verify_2fa')
                    else:
                        # No 2FA, log in directly
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