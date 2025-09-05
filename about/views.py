from django.shortcuts import render
from django.http import HttpResponse

def about_page(request):
    """Сторінка 'Про нас'"""
    context = {
        'page_title': 'About Lazysoft',
        'page_description': 'The story of how laziness became a philosophy, a tech stack, and an efficient business model.',
    }
    return render(request, 'about/about.html', context)
