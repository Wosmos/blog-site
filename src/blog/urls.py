from django.urls import path
from . import auth_views, views

app_name = 'blog'

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.blog_admin_login, name='admin_login'),
    path('logout/', auth_views.blog_admin_logout, name='admin_logout'),
    
    # Admin dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Blog CRUD URLs
    path('posts/', views.BlogListView.as_view(), name='list'),
    path('posts/create/', views.BlogCreateView.as_view(), name='create'),
    path('posts/<slug:slug>/', views.BlogDetailView.as_view(), name='detail'),
    path('posts/<slug:slug>/edit/', views.BlogUpdateView.as_view(), name='update'),
]