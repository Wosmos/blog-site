from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # Public views
    path('', views.PublicBlogListView.as_view(), name='home'),
    path('blog/<slug:slug>/', views.PublicBlogDetailView.as_view(), name='public_detail'),
    
    # Admin views (namespaced)
    path('admin/', include('blog.urls')),
    
    # Django built-in admin
    path('django-admin/', admin.site.urls),
]