from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.contrib import messages
import markdown
from .auth_views import admin_required
from .models import BlogPost
from .forms import BlogPostForm


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


class BlogListView(LoginRequiredMixin, ListView):
    """
    Blog list view with pagination, search, and filtering functionality.
    Displays all blog posts with admin controls.
    """
    model = BlogPost
    template_name = 'blog/admin/blog_list.html'
    context_object_name = 'blog_posts'
    paginate_by = 10
    login_url = 'blog:admin_login'
    
    def get_queryset(self):
        """
        Get filtered and searched queryset based on request parameters.
        """
        queryset = BlogPost.objects.select_related('author').order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(author__username__icontains=search_query) |
                Q(author__first_name__icontains=search_query) |
                Q(author__last_name__icontains=search_query)
            )
        
        # Status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter and status_filter in ['draft', 'published']:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'All Blog Posts'
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        
        # Use paginator count to avoid extra query
        if hasattr(context.get('paginator'), 'count'):
            context['total_posts'] = context['paginator'].count
        else:
            context['total_posts'] = self.get_queryset().count()
        
        # Add status choices for filter dropdown
        context['status_choices'] = BlogPost.STATUS_CHOICES
        
        return context


class BlogCreateView(LoginRequiredMixin, CreateView):
    """
    Blog create view with form validation and slug auto-generation.
    Allows authenticated users to create new blog posts.
    """
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/admin/blog_create.html'
    login_url = 'blog:admin_login'
    success_url = reverse_lazy('blog:list')
    
    def get_form_kwargs(self):
        """
        Pass the current user to the form.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        """
        response = super().form_valid(form)
        
        # Add success message
        messages.success(
            self.request,
            f'Blog post "{self.object.title}" has been created successfully!'
        )
        
        return response
    
    def form_invalid(self, form):
        """
        Handle form validation errors.
        """
        messages.error(
            self.request,
            'There were errors in your form. Please correct them and try again.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Blog Post'
        context['submit_text'] = 'Create Post'
        context['cancel_url'] = reverse_lazy('blog:list')
        return context


class BlogDetailView(LoginRequiredMixin, DetailView):
    """
    Blog detail view for individual post display with markdown rendering.
    Provides preview functionality for blog posts.
    """
    model = BlogPost
    template_name = 'blog/admin/blog_detail.html'
    context_object_name = 'blog_post'
    login_url = 'blog:admin_login'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Get queryset with author information for performance.
        """
        return BlogPost.objects.select_related('author')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        blog_post = self.object
        
        # Render markdown content
        md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
        ])
        context['rendered_content'] = md.convert(blog_post.content)
        
        # Navigation between posts
        context['previous_post'] = BlogPost.objects.filter(
            created_at__lt=blog_post.created_at
        ).order_by('-created_at').first()
        
        context['next_post'] = BlogPost.objects.filter(
            created_at__gt=blog_post.created_at
        ).order_by('created_at').first()
        
        # Additional context
        context['title'] = f'Preview: {blog_post.title}'
        context['list_url'] = reverse_lazy('blog:list')
        
        return context


class BlogUpdateView(LoginRequiredMixin, UpdateView):
    """
    Blog update view with pre-populated forms and update timestamp handling.
    Allows authenticated users to edit existing blog posts.
    """
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/admin/blog_update.html'
    context_object_name = 'blog_post'
    login_url = 'blog:admin_login'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Get queryset with author information for performance.
        """
        return BlogPost.objects.select_related('author')
    
    def get_form_kwargs(self):
        """
        Pass the current user to the form.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """
        Handle successful form submission with update timestamp.
        """
        # The updated_at field will be automatically updated by the model
        response = super().form_valid(form)
        
        # Add success message
        messages.success(
            self.request,
            f'Blog post "{self.object.title}" has been updated successfully!'
        )
        
        return response
    
    def form_invalid(self, form):
        """
        Handle form validation errors.
        """
        messages.error(
            self.request,
            'There were errors in your form. Please correct them and try again.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        """
        Redirect to the detail view of the updated post.
        """
        return reverse_lazy('blog:detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        blog_post = self.object
        
        context['title'] = f'Edit: {blog_post.title}'
        context['submit_text'] = 'Update Post'
        context['cancel_url'] = reverse_lazy('blog:detail', kwargs={'slug': blog_post.slug})
        context['list_url'] = reverse_lazy('blog:list')
        
        return context
