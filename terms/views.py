from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import StaticPage

def static_page_view(request, slug):
    try:
        page = get_object_or_404(StaticPage, slug=slug, is_active=True)
    except StaticPage.DoesNotExist:
        raise Http404("Page not found")
    
    context = {
        'page': page,
        'page_title': page.safe_translation_getter('title', slug.title()),
        'page_content': page.safe_translation_getter('content', ''),
        'meta_description': page.safe_translation_getter('meta_description', ''),
    }
    
    return render(request, 'terms/static_page.html', context)