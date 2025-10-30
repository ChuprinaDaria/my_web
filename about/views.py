from django.shortcuts import render
from django.utils.translation import get_language
from .models import About

def about_page(request):
    """Сторінка 'Про нас'"""
    # Спробуємо знайти активний запис About
    try:
        about = About.objects.filter(is_active=True).first()
        if not about:
            # Якщо немає активного запису, створимо запис за замовчуванням
            about = About.objects.create(
                title_en="About Lazysoft",
                title_uk="Про Lazysoft", 
                title_pl="O Lazysoft",
                subtitle_en="We specialize in AI automation solutions",
                subtitle_uk="Ми спеціалізуємося на рішеннях з автоматизації ШІ",
                subtitle_pl="Specjalizujemy się w rozwiązaniach automatyzacji AI",
                story_en="<p>Lazysoft is a leading company in AI automation solutions...</p>",
                story_uk="<p>Lazysoft - провідна компанія в галузі рішень автоматизації ШІ...</p>",
                story_pl="<p>Lazysoft to wiodąca firma w dziedzinie rozwiązań automatyzacji AI...</p>",
                services_en="<p>We provide comprehensive AI automation services...</p>",
                services_uk="<p>Ми надаємо комплексні послуги автоматизації ШІ...</p>",
                services_pl="<p>Oferujemy kompleksowe usługi automatyzacji AI...</p>",
                mission_en="<p>Our mission is to transform businesses through smart automation...</p>",
                mission_uk="<p>Наша місія - трансформувати бізнес за допомогою розумної автоматизації...</p>",
                mission_pl="<p>Nasza misja to transformacja biznesu poprzez inteligentną automatyzację...</p>",
                is_active=True
            )
    except Exception as e:
        # Якщо щось пішло не так, створимо мінімальний запис
        about = About.objects.create(
            title_en="About Lazysoft",
            title_uk="Про Lazysoft", 
            title_pl="O Lazysoft",
            is_active=True
        )
    
    current_language = get_language()
    
    # OG-теги для соцмереж
    og_title = getattr(about, f'title_{current_language}') or about.title_en
    og_description = getattr(about, f'subtitle_{current_language}') or about.subtitle_en or ''
    og_image_url = None

    # Перевіряємо чи є og_image
    if hasattr(about, 'og_image') and about.og_image:
        og_image_url = request.build_absolute_uri(about.og_image.url)
    # Якщо немає og_image, використовуємо gallery зображення по черзі
    elif about.gallery_image_1:
        og_image_url = request.build_absolute_uri(about.gallery_image_1.url)
    elif about.gallery_image_2:
        og_image_url = request.build_absolute_uri(about.gallery_image_2.url)
    elif about.gallery_image_3:
        og_image_url = request.build_absolute_uri(about.gallery_image_3.url)

    # Динамічний контент залежно від мови
    # Галерея: поєднуємо 3 поля About + пов'язані AboutImage
    gallery = []
    # Спершу основні 3 зображення
    if about.gallery_image_1:
        gallery.append({'url': about.gallery_image_1.url, 'alt': 'About Gallery 1'})
    if about.gallery_image_2:
        gallery.append({'url': about.gallery_image_2.url, 'alt': 'About Gallery 2'})
    if about.gallery_image_3:
        gallery.append({'url': about.gallery_image_3.url, 'alt': 'About Gallery 3'})

    # Додаємо додаткові зображення з AboutImage у визначеному порядку
    try:
        for img in about.images.filter(is_active=True).order_by('order'):
            alt = getattr(img, f'alt_text_{current_language}', None) or img.alt_text_en or ''
            gallery.append({'url': img.image.url, 'alt': alt})
    except Exception:
        pass

    context = {
        'about': about,
        'page_title': getattr(about, f'seo_title_{current_language}') or getattr(about, f'title_{current_language}'),
        'page_description': getattr(about, f'seo_description_{current_language}') or getattr(about, f'subtitle_{current_language}'),
        'current_language': current_language,
        'gallery': gallery,
        # OG-теги для соцмереж
        'og_title': og_title,
        'og_description': og_description,
        'og_image': og_image_url,
        'og_url': request.build_absolute_uri(),
        # Breadcrumbs для structured data
        'breadcrumbs': [
            {
                'name': getattr(about, f'title_{current_language}') or about.title_en or 'About',
                'url': request.path
            }
        ]
    }
    return render(request, 'about/about.html', context)
