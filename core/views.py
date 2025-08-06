from django.shortcuts import render as django_render
from django.shortcuts import render
from django.utils.translation import get_language
from projects.models import Project

def home(request):
    # Отримуємо featured проєкти для головної сторінки
    featured_projects = Project.objects.filter(
        is_active=True, 
        is_featured=True
    ).order_by('-order', '-project_date')[:6]  # Показуємо до 6 проєктів
    
    context = {
        'featured_projects': featured_projects
    }
    return django_render(request, 'core/home.html', context)

def about_view(request):
    lang = get_language()[:2]  # en, uk, pl
    template_name = f"core/about_{lang}.html"
    return render(request, template_name)