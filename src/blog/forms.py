from django import forms
from django.utils.text import slugify
from .models import BlogPost


class BlogPostForm(forms.ModelForm):
    """
    Form for creating and editing blog posts.
    """
    
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'excerpt', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter blog post title...',
                'maxlength': 200,
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control markdown-editor',
                'placeholder': 'Write your blog post content in Markdown...',
                'rows': 15,
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional excerpt for the blog post...',
                'rows': 3,
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        help_texts = {
            'title': 'The title of your blog post (max 200 characters)',
            'content': 'Write your blog post content using Markdown formatting',
            'excerpt': 'Optional short description or excerpt for the post',
            'status': 'Choose whether to save as draft or publish immediately',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Store original title for slug regeneration logic
        self.original_title = getattr(self.instance, 'title', None) if self.instance and self.instance.pk else None
        
        # Make excerpt optional in the form
        self.fields['excerpt'].required = False
        
        # Add custom validation messages
        self.fields['title'].error_messages = {
            'required': 'Please enter a title for your blog post.',
            'max_length': 'Title must be 200 characters or less.',
        }
        
        self.fields['content'].error_messages = {
            'required': 'Please enter content for your blog post.',
        }
    
    def clean_title(self):
        """
        Validate and clean the title field.
        """
        title = self.cleaned_data.get('title')
        
        if not title:
            raise forms.ValidationError('Title is required.')
        
        # Check for title uniqueness (excluding current instance if editing)
        slug = slugify(title)
        existing_posts = BlogPost.objects.filter(slug=slug)
        
        if self.instance and self.instance.pk:
            existing_posts = existing_posts.exclude(pk=self.instance.pk)
        
        if existing_posts.exists():
            # Check if we can create a unique slug by appending numbers
            counter = 1
            original_slug = slug
            while existing_posts.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
                if counter > 100:  # Prevent infinite loop
                    raise forms.ValidationError(
                        'A blog post with a similar title already exists. '
                        'Please choose a different title.'
                    )
        
        return title
    
    def clean_content(self):
        """
        Validate and clean the content field.
        """
        content = self.cleaned_data.get('content')
        
        if not content or not content.strip():
            raise forms.ValidationError('Content cannot be empty.')
        
        # Basic content length validation
        if len(content) < 10:
            raise forms.ValidationError(
                'Content must be at least 10 characters long.'
            )
        
        return content.strip()
    
    def clean_excerpt(self):
        """
        Validate and clean the excerpt field.
        """
        excerpt = self.cleaned_data.get('excerpt', '')
        
        if excerpt:
            excerpt = excerpt.strip()
            if len(excerpt) > 500:
                raise forms.ValidationError(
                    'Excerpt must be 500 characters or less.'
                )
        
        return excerpt
    
    def save(self, commit=True):
        """
        Save the blog post with proper author assignment and slug generation.
        """
        blog_post = super().save(commit=False)
        
        # Set the author if creating a new post
        if not blog_post.pk and self.user:
            blog_post.author = self.user
        
        # Generate or regenerate slug based on title
        # For new posts or when title changes, regenerate slug
        title_changed = self.original_title and self.original_title != blog_post.title
        
        if not blog_post.slug or not blog_post.pk or title_changed:
            blog_post.slug = slugify(blog_post.title)
            
            # Ensure slug uniqueness
            original_slug = blog_post.slug
            counter = 1
            while BlogPost.objects.filter(slug=blog_post.slug).exclude(pk=blog_post.pk).exists():
                blog_post.slug = f"{original_slug}-{counter}"
                counter += 1
        
        if commit:
            blog_post.save()
        
        return blog_post