from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from .models import Product


def product_list(request):
    """Список всіх активних продуктів"""
    products = Product.objects.filter(is_active=True)
    lang = get_language() or 'uk'

    # Підготовка даних для шаблону
    products_data = []
    for product in products:
        products_data.append({
            'object': product,
            'title': product.get_title(lang),
            'short_description': product.get_short_description(lang),
            'url': product.get_absolute_url(lang),
            'image': product.featured_image,
            'icon': product.icon,
            'cta_text': product.get_cta_text(lang),
            'cta_url': product.cta_url,
            'packages_count': product.pricing_packages.filter(is_active=True).count(),
        })

    context = {
        'products': products_data,
        'products_raw': products,  # Для сумісності з шаблонами
        'CURRENT_LANG': lang,
    }

    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    """Детальна сторінка продукту"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    lang = get_language() or 'uk'

    # Отримуємо пакети цін
    pricing_packages = product.pricing_packages.filter(is_active=True).order_by('order', 'price')

    # Отримуємо відгуки
    reviews = product.reviews.filter(is_active=True).order_by('-is_featured', '-rating', '-date_created')

    # Пов'язаний контент
    related_services = product.related_services.all()[:3]
    related_projects = product.get_related_projects(limit=3)
    related_articles = product.get_related_articles(limit=3)

    # Галерея
    gallery_images = product.get_gallery_images()

    context = {
        'product': product,
        'CURRENT_LANG': lang,

        # Переклади
        'title': product.get_title(lang),
        'short_description': product.get_short_description(lang),
        'description': product.get_description(lang),
        'target_audience': product.get_target_audience(lang),
        'features': product.get_features(lang),
        'how_it_works': product.get_how_it_works(lang),
        'cta_text': product.get_cta_text(lang),

        # Медіа
        'gallery_images': gallery_images,

        # Ціни та пакети
        'pricing_packages': pricing_packages,

        # Відгуки
        'reviews': reviews,

        # Пов'язаний контент
        'related_services': related_services,
        'related_projects': related_projects,
        'related_articles': related_articles,

        # SEO
        'seo_title': product.get_seo_title(lang),
        'seo_description': product.get_seo_description(lang),
        'og_image': product.og_image,
    }

    return render(request, 'products/product_detail.html', context)
