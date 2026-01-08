from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form with email field.
    """
    email = forms.EmailField(required=True, help_text='Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=True, help_text='Enter your first name.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Enter your last name.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add classes to form fields for styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full pl-11 pr-4 py-3 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-md text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-600 focus:outline-none focus:ring-2 focus:ring-stone-900 dark:focus:ring-indigo-500 focus:bg-white dark:focus:bg-stone-800 input-transition sm:text-sm'
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class TwoFactorForm(forms.Form):
    """
    Form for entering 2FA verification code.
    """
    token = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-4 pr-4 py-3 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-md text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-600 focus:outline-none focus:ring-2 focus:ring-stone-900 dark:focus:ring-indigo-500 focus:bg-white dark:focus:bg-stone-800 input-transition sm:text-sm text-center text-2xl tracking-widest',
            'placeholder': '0 0 0 0 0 0',
            'maxlength': '6',
            'autocomplete': 'off',
            'autofocus': 'true'
        }),
        help_text='Enter the 6-digit code from your authenticator app.'
    )

    def clean_token(self):
        token = self.cleaned_data.get('token', '').strip()
        if not token.isdigit() or len(token) != 6:
            raise forms.ValidationError('Please enter a valid 6-digit code.')
        return token


class ForgotPasswordForm(forms.Form):
    """
    Form for initiating password reset.
    """
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'block w-full pl-11 pr-4 py-3 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-md text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-600 focus:outline-none focus:ring-2 focus:ring-stone-900 dark:focus:ring-indigo-500 focus:bg-white dark:focus:bg-stone-800 input-transition sm:text-sm',
            'placeholder': 'Enter your email address',
            'required': 'required'
        }),
        help_text='Enter your email address to receive a password reset link.'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('No account found with this email address.')
        return email


class ResetPasswordForm(forms.Form):
    """
    Form for resetting password after verification.
    """
    password1 = forms.CharField(
        label='New Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-11 pr-4 py-3 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-md text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-600 focus:outline-none focus:ring-2 focus:ring-stone-900 dark:focus:ring-indigo-500 focus:bg-white dark:focus:bg-stone-800 input-transition sm:text-sm',
            'placeholder': 'Enter new password',
            'required': 'required'
        }),
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-11 pr-4 py-3 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-md text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-600 focus:outline-none focus:ring-2 focus:ring-stone-900 dark:focus:ring-indigo-500 focus:bg-white dark:focus:bg-stone-800 input-transition sm:text-sm',
            'placeholder': 'Confirm new password',
            'required': 'required'
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        
        return cleaned_data


class TwoFactorSetupForm(forms.Form):
    """
    Form for confirming 2FA setup.
    """
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-4 pr-4 py-3 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-md text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-600 focus:outline-none focus:ring-2 focus:ring-stone-900 dark:focus:ring-indigo-500 focus:bg-white dark:focus:bg-stone-800 input-transition sm:text-sm text-center text-2xl tracking-widest',
            'placeholder': '0 0 0 0 0 0',
            'maxlength': '6',
            'autocomplete': 'off',
            'autofocus': 'true'
        }),
        help_text='Enter the 6-digit code from your authenticator app to confirm setup.'
    )

    def clean_verification_code(self):
        verification_code = self.cleaned_data.get('verification_code', '').strip()
        if not verification_code.isdigit() or len(verification_code) != 6:
            raise forms.ValidationError('Please enter a valid 6-digit code.')
        return verification_code