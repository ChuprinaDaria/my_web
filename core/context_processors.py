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
