"""
🔧 Context Processors для глобальних змінних
"""


def cookie_consent(request):
    """
    Додаємо інформацію про cookie consent у всі шаблони
    """
    # Якщо middleware додано, використовуємо його дані
    if hasattr(request, 'cookie_consent'):
        return {
            'cookie_consent': request.cookie_consent
        }
    
    # Fallback якщо middleware не працює
    consent_cookie = request.COOKIES.get('cookie_consent', None)
    
    return {
        'cookie_consent': {
            'has_consent': consent_cookie in ['accepted', 'declined'],
            'is_accepted': consent_cookie == 'accepted',
            'is_declined': consent_cookie == 'declined',
            'show_banner': consent_cookie is None,
        }
    }

from django.conf import settings

def seo_settings(request):
    """Додає SEO налаштування в контекст шаблонів"""
    from django.utils import translation
    
    # Визначаємо тип сторінки для schema.org
    page_type = 'home'
    breadcrumbs = []
    
    # Визначаємо тип сторінки на основі URL
    path = request.path
    if '/news/' in path:
        page_type = 'news'
    elif '/projects/' in path:
        page_type = 'projects'
    elif '/services/' in path:
        page_type = 'services'
    elif '/contact' in path:
        page_type = 'contact'
    elif '/about' in path:
        page_type = 'about'
    
    # Створюємо breadcrumbs
    current_lang = translation.get_language()
    breadcrumbs = [
        {
            'name': 'Home' if current_lang == 'en' else ('Головна' if current_lang == 'uk' else 'Strona główna'),
            'url': f'/{current_lang}/' if current_lang != 'en' else '/'
        }
    ]
    
    # Додаємо додаткові breadcrumbs залежно від сторінки
    if page_type == 'news':
        breadcrumbs.append({
            'name': 'News' if current_lang == 'en' else ('Новини' if current_lang == 'uk' else 'Aktualności'),
            'url': f'/{current_lang}/news/' if current_lang != 'en' else '/news/'
        })
    elif page_type == 'projects':
        breadcrumbs.append({
            'name': 'Projects' if current_lang == 'en' else ('Проекти' if current_lang == 'uk' else 'Projekty'),
            'url': f'/{current_lang}/projects/' if current_lang != 'en' else '/projects/'
        })
    elif page_type == 'services':
        breadcrumbs.append({
            'name': 'Services' if current_lang == 'en' else ('Послуги' if current_lang == 'uk' else 'Usługi'),
            'url': f'/{current_lang}/services/' if current_lang != 'en' else '/services/'
        })
    
    return {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'GOOGLE_SITE_VERIFICATION': settings.GOOGLE_SITE_VERIFICATION,
        'BING_SITE_VERIFICATION': settings.BING_SITE_VERIFICATION,
        'YAHOO_SITE_VERIFICATION': settings.YAHOO_SITE_VERIFICATION,
        'DISABLE_GOOGLE_INDEXING': settings.DISABLE_GOOGLE_INDEXING,
        'SITE_URL': settings.SITE_URL,
        'SITE_NAME': settings.SITE_NAME,
        'page_type': page_type,
        'breadcrumbs': breadcrumbs,
    }
