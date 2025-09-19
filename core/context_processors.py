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
    return {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'GOOGLE_SITE_VERIFICATION': settings.GOOGLE_SITE_VERIFICATION,
        'BING_SITE_VERIFICATION': settings.BING_SITE_VERIFICATION,
        'YAHOO_SITE_VERIFICATION': settings.YAHOO_SITE_VERIFICATION,
        'DISABLE_GOOGLE_INDEXING': settings.DISABLE_GOOGLE_INDEXING,
        'SITE_URL': settings.SITE_URL,
        'SITE_NAME': settings.SITE_NAME,
    }
