from django.http import HttpResponse


def home_page_view(request, *args, **kwargs):
    return HttpResponse("<H1>hi bro</h1>")