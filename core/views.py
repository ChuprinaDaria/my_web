from django.shortcuts import render as django_render
from django.shortcuts import render
from django.utils.translation import get_language

def home(request):
    return django_render(request, 'core/home.html')

def projects(request):
    return django_render(request, 'core/projects.html')

def about_view(request):
    lang = get_language()[:2]  # en, uk, pl
    template_name = f"core/about_{lang}.html"
    return render(request, template_name)