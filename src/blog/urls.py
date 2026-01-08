from django.urls import path
from . import auth_views, views

app_name = 'blog'

urlpatterns = [
    # Authentication URLs
    path('register/', auth_views.register, name='register'),
    path('login/', auth_views.blog_admin_login, name='admin_login'),
    path('logout/', auth_views.blog_admin_logout, name='admin_logout'),
    path('verify-email/<str:token>/', auth_views.verify_email, name='verify_email'),
    path('forgot-password/', auth_views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', auth_views.reset_password, name='reset_password'),
    path('setup-2fa/', auth_views.setup_2fa, name='setup_2fa'),
    path('disable-2fa/', auth_views.disable_2fa, name='disable_2fa'),
    path('verify-2fa/', auth_views.verify_2fa, name='verify_2fa'),

    # Admin dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),

    # Blog CRUD URLs
    path('posts/', views.BlogListView.as_view(), name='list'),
    path('posts/create/', views.BlogCreateView.as_view(), name='create'),
    path('posts/<slug:slug>/', views.BlogDetailView.as_view(), name='detail'),
    path('posts/<slug:slug>/edit/', views.BlogUpdateView.as_view(), name='update'),
]