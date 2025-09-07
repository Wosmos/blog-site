from django.urls import path
from . import auth_views, views

app_name = 'blog'

urlpatterns = [
    # Authentication URLs
    path('admin/login/', auth_views.blog_admin_login, name='admin_login'),
    path('admin/logout/', auth_views.blog_admin_logout, name='admin_logout'),
    
    # Admin dashboard (placeholder for now)
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]