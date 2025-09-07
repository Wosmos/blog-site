from django.shortcuts import render
from .auth_views import admin_required


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
