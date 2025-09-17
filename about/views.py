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
    
    # Динамічний контент залежно від мови
    context = {
        'about': about,
        'page_title': getattr(about, f'seo_title_{current_language}') or getattr(about, f'title_{current_language}'),
        'page_description': getattr(about, f'seo_description_{current_language}') or getattr(about, f'subtitle_{current_language}'),
        'current_language': current_language,
    }
    return render(request, 'about/about.html', context)
