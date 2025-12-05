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
        'products_list': products,  # Для JSON-LD ItemList схеми
        'CURRENT_LANG': lang,
        
        # Breadcrumbs для schema.org
        'breadcrumbs': [
            {
                'name': 'Products' if lang == 'en' else ('Продукти' if lang == 'uk' else 'Produkty'),
                'url': request.path
            }
        ]
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

    # Пов'язаний контент - підготовка з локалізацією
    related_services_raw = product.related_services.all()[:3]
    related_services_data = []
    for service in related_services_raw:
        # Отримуємо локалізовану назву
        service_title = getattr(service, f'title_{lang}', None) or getattr(service, 'title_en', '')
        related_services_data.append({
            'object': service,
            'slug': service.slug,
            'title': service_title,
        })
    
    related_projects_raw = product.get_related_projects(limit=3)
    related_projects_data = []
    for project in related_projects_raw:
        # Отримуємо локалізовану назву та URL
        project_title = getattr(project, f'title_{lang}', None) or getattr(project, 'title_en', '')
        project_url = project.get_absolute_url(lang)
        related_projects_data.append({
            'object': project,
            'slug': project.slug,
            'title': project_title,
            'url': project_url,
        })
    
    related_articles_raw = product.get_related_articles(limit=3)
    related_articles_data = []
    for article in related_articles_raw:
        # Отримуємо локалізовану назву та URL
        if hasattr(article, 'get_title'):
            article_title = article.get_title(lang)
        else:
            article_title = getattr(article, f'title_{lang}', None) or getattr(article, 'title_uk', '')
        
        if hasattr(article, 'get_absolute_url'):
            article_url = article.get_absolute_url()
        else:
            article_url = f'/news/{article.slug}/'
        
        related_articles_data.append({
            'object': article,
            'slug': article.slug,
            'title': article_title,
            'url': article_url,
        })

    # Галерея
    gallery_images = product.get_gallery_images()

    # Обчислюємо середній рейтинг для aggregateRating
    aggregate_rating = None
    if reviews_data:
        total_rating = sum(review['rating'] for review in reviews_data)
        avg_rating = total_rating / len(reviews_data) if reviews_data else 5.0
        aggregate_rating = round(avg_rating, 1)

    # Обчислюємо lowPrice та highPrice для AggregateOffer
    low_price = None
    high_price = None
    price_currency = None
    if packages_data:
        # Збираємо всі ціни (price_from та price_to якщо є)
        prices = []
        for pkg in packages_data:
            pkg_obj = pkg['object']
            if hasattr(pkg_obj, 'price_from') and pkg_obj.price_from:
                prices.append(float(pkg_obj.price_from))
            if hasattr(pkg_obj, 'price_to') and pkg_obj.price_to:
                prices.append(float(pkg_obj.price_to))
            # Якщо немає price_from/price_to, спробуємо price
            elif hasattr(pkg_obj, 'price') and pkg_obj.price:
                prices.append(float(pkg_obj.price))
        
        if prices:
            low_price = min(prices)
            high_price = max(prices)
            # Отримуємо валюту з першого пакету
            first_pkg = packages_data[0]['object']
            if hasattr(first_pkg, 'currency'):
                price_currency = first_pkg.currency
            else:
                price_currency = 'USD'  # fallback

    context = {
        'product': product,  # Передаємо product для JSON-LD схеми
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
        'low_price': low_price,
        'high_price': high_price,
        'price_currency': price_currency,

        # Відгуки
        'reviews': reviews_data,
        'reviews_raw': reviews,  # Для JSON-LD
        'aggregate_rating': aggregate_rating,
        'reviews_count': len(reviews_data),  # Для JSON-LD

        # Пов'язаний контент (локалізований)
        'related_services': related_services_data,
        'related_projects': related_projects_data,
        'related_articles': related_articles_data,

        # SEO
        'seo_title': product.get_seo_title(lang),
        'seo_description': product.get_seo_description(lang),
        'og_image': product.og_image,
        
        # Breadcrumbs для schema.org
        'breadcrumbs': [
            {
                'name': 'Products' if lang == 'en' else ('Продукти' if lang == 'uk' else 'Produkty'),
                'url': f'/{lang}/products/' if lang != 'en' else '/products/'
            },
            {
                'name': product.get_title(lang),
                'url': product.get_absolute_url(lang)
            }
        ]
    }

    return render(request, 'products/product_detail.html', context)
