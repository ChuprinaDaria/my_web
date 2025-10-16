# lazysoft/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from django.shortcuts import redirect
from django.utils.translation import get_language
from django.http import HttpResponse

# 📰 Імпортуємо sitemaps для SEO
try:
    from core.sitemaps import (
        StaticViewSitemap, 
        ServiceDetailSitemap, 
        ProjectDetailSitemap, 
        ArticleDetailSitemap,
        NewsSitemap,
        NewsCategorySitemap
    )
    from news.sitemaps import NewsUkrainianSitemap, NewsPolishSitemap, NewsEnglishSitemap
    SITEMAPS_AVAILABLE = True
except ImportError:
    SITEMAPS_AVAILABLE = False
    print("⚠️ News sitemaps not available - run migrations first")


# 🔁 Сумісність: редірект зі старого /admin/ на новий /<lang>/control/
def redirect_admin(request):
    lang = get_language() or 'pl'
    return redirect(f'/{lang}/control/')

# 🔁 Короткі URL без мовного префікса → редірект на поточну мову
def redirect_privacy_policy(request):
    lang = get_language() or 'pl'
    return redirect('/legal/privacy-policy/' if lang == 'en' else f'/{lang}/legal/privacy-policy/')

def redirect_terms_of_service(request):
    lang = get_language() or 'pl'
    return redirect('/legal/terms-of-service/' if lang == 'en' else f'/{lang}/legal/terms-of-service/')

def redirect_cookies_policy(request):
    lang = get_language() or 'pl'
    return redirect('/legal/cookies-policy/' if lang == 'en' else f'/{lang}/legal/cookies-policy/')

urlpatterns = []

urlpatterns += [
    path('admin/', redirect_admin, name='admin_legacy_redirect'),
    path('privacy-policy/', redirect_privacy_policy, name='privacy_policy_short'),
    path('terms-of-service/', redirect_terms_of_service, name='terms_of_service_short'),
    path('cookies-policy/', redirect_cookies_policy, name='cookies_policy_short'),
    # path('', simple_home_view, name='simple_home'),  # Перенесено на початок
]

# 🗺️ Sitemap (без i18n-префіксів)
if SITEMAPS_AVAILABLE:
    sitemaps = {
        'static': StaticViewSitemap,
        'services': ServiceDetailSitemap,
        'projects': ProjectDetailSitemap,
        'articles': ArticleDetailSitemap,
        'news': NewsSitemap,
        'news_categories': NewsCategorySitemap,
    }
    urlpatterns += [
        path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
        path('sitemap-static.xml', sitemap, {'sitemaps': {'static': StaticViewSitemap}}, name='static_sitemap'),
        path('sitemap-services.xml', sitemap, {'sitemaps': {'services': ServiceDetailSitemap}}, name='services_sitemap'),
        path('sitemap-projects.xml', sitemap, {'sitemaps': {'projects': ProjectDetailSitemap}}, name='projects_sitemap'),
        path('sitemap-articles.xml', sitemap, {'sitemaps': {'articles': ArticleDetailSitemap}}, name='articles_sitemap'),
        path('sitemap-news.xml', sitemap, {'sitemaps': {'news': NewsSitemap}}, name='news_sitemap'),
        path('sitemap-categories.xml', sitemap, {'sitemaps': {'news_categories': NewsCategorySitemap}}, name='categories_sitemap'),
        # Google News Sitemaps - окремі для кожної мови
        path('news-sitemap-uk.xml', sitemap, {'sitemaps': {'news': NewsUkrainianSitemap}}, name='news-sitemap-uk'),
        path('news-sitemap-pl.xml', sitemap, {'sitemaps': {'news': NewsPolishSitemap}}, name='news-sitemap-pl'),
        path('news-sitemap-en.xml', sitemap, {'sitemaps': {'news': NewsEnglishSitemap}}, name='news-sitemap-en'),
    ]

# robots.txt (без i18n) - ВІДКЛЮЧЕНО НА DEV
# ВАЖЛИВО: використовуємо пряму view з core.urls
# 🚫 На розробці robots.txt може заважати тестуванню, тому відключаємо
if not settings.DEBUG:  # Тільки на production
    from core.views import robots_txt
    urlpatterns += [
        path('robots.txt', robots_txt, name='robots'),
    ]

# 🔐 2FA (БЕЗ i18n!) - УВІМКНЕНО
# КАНОН: не імпортуємо список, просто include модуля
urlpatterns += [
    path('account/', include('django.contrib.auth.urls')),
]

# 🔤 Усе, що має мовні префікси
from core.views_2fa import TwoFactorLoginView, TwoFactorSetupView

# 🌐 Django i18n URL для зміни мови (ПЕРЕД i18n_patterns!)
from django.conf.urls.i18n import i18n_patterns
urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('control/login/', TwoFactorLoginView.as_view(), name='admin_2fa_login'),
    path('control/2fa/setup/', TwoFactorSetupView.as_view(), name='2fa_setup'),
    path('control/', admin.site.urls),
    path('', include(('core.urls', 'core'), namespace='core')),
    path('', include('lazysoft.dashboard_urls')),
    path('projects/', include('projects.urls')),
    path('services/', include(('services.urls', 'services'), namespace='services')),
    path('about/', include('about.urls')),
    path('news/', include(('news.urls', 'news'), namespace='news')),
    path('consultant/', include('consultant.urls')),
    path('contacts/', include('contacts.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('legal/', include('terms.urls')),
    prefix_default_language=False,  # Тимчасово для діагностики
)

# Статика/медіа у DEBUG
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'core.views.error_400'
handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'