from django.shortcuts import render
from django.http import HttpResponse
from .auth_views import admin_required


def home_page_view(request):
    """
    Home page view for the blog application.
    """
    return HttpResponse("<h1>Welcome to the Blog Admin System</h1><p><a href='/admin/'>Go to Admin</a></p>")


@admin_required
def admin_dashboard(request):
    """
    Blog admin dashboard view.
    Displays overview of blog management interface.
    """
    return render(request, 'blog/admin/dashboard.html', {
        'title': 'Blog Admin Dashboard',
        'user': request.user,
    })
