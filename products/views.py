from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from .models import Product


def product_list(request):
    """Список всіх активних продуктів"""
    products = Product.objects.filter(is_active=True).order_by('-priority', 'order')
    lang = get_language() or 'uk'

    # Підготовка даних для шаблону
    products_data = []
    for product in products:
        products_data.append({
            'object': product,
            'title': product.get_title(lang),
            'short_description': product.get_short_description(lang) or '',
            'url': product.get_absolute_url(lang),
            'image': product.featured_image,
            'icon': product.icon,
            'cta_text': product.get_cta_text(lang),
            'cta_url': product.cta_url,
            'packages_count': product.pricing_packages.filter(is_active=True).count(),
        })

    context = {
        'products': products_data,
        'products_raw': products,
        'CURRENT_LANG': lang,
    }

    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    """Детальна сторінка продукту"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    lang = get_language() or 'uk'

    # Отримуємо пакети цін
    pricing_packages = product.pricing_packages.filter(is_active=True).order_by('order', 'price')

    # Підготуємо дані пакетів з перекладами
    packages_data = []
    for package in pricing_packages:
        packages_data.append({
            'object': package,
            'name': package.get_name(lang),
            'description': package.get_description(lang),
            'features': package.get_features(lang),
            'price_display': package.get_price_display(),
            'billing_period': package.get_billing_period_display_translated(lang),
            'is_recommended': package.is_recommended,
            'has_trial': package.has_trial,
            'trial_days': package.trial_days,
        })

    # Отримуємо відгуки
    reviews = product.reviews.filter(is_active=True).order_by('-is_featured', '-rating', '-date_created')

    # Підготуємо дані відгуків з перекладами
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'object': review,
            'review_text': review.get_review_text(lang),
            'author_name': review.author_name,
            'author_position': review.author_position,
            'author_company': review.author_company,
            'author_avatar': review.author_avatar,
            'rating': review.rating,
        })

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
        'short_description': product.get_short_description(lang) or '',
        'description': product.get_description(lang) or '',
        'target_audience': product.get_target_audience(lang) or '',
        'features': product.get_features(lang) or '',
        'how_it_works': product.get_how_it_works(lang) or '',
        'cta_text': product.get_cta_text(lang),

        # Медіа
        'gallery_images': gallery_images,

        # Ціни та пакети
        'pricing_packages': packages_data,

        # Відгуки
        'reviews': reviews_data,

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
