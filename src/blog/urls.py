from django.urls import path
from . import auth_views, views

app_name = 'blog'

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.blog_admin_login, name='admin_login'),
    path('logout/', auth_views.blog_admin_logout, name='admin_logout'),
    
    # Admin dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
]