# lazysoft/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap

# 📰 Імпортуємо sitemaps для SEO
try:
    from news.views import NewsSitemap, NewsCategorySitemap
    SITEMAPS_AVAILABLE = True
except ImportError:
    SITEMAPS_AVAILABLE = False
    print("⚠️ News sitemaps not available - run migrations first")

urlpatterns = []

# 🗺️ Sitemap (без i18n-префіксів)
if SITEMAPS_AVAILABLE:
    sitemaps = {
        'news': NewsSitemap,
        'news_categories': NewsCategorySitemap,
    }
    urlpatterns += [
        path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
        path('sitemap-news.xml', sitemap, {'sitemaps': {'news': NewsSitemap}}, name='news_sitemap'),
        path('sitemap-categories.xml', sitemap, {'sitemaps': {'categories': NewsCategorySitemap}}, name='categories_sitemap'),
    ]

# robots.txt (без i18n)
urlpatterns += [
    path('robots.txt', include('core.urls')),
]

# 🔤 URL з мовними префіксами
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('projects/', include('projects.urls')),
    path('services/', include(('services.urls', 'services'), namespace='services')),
    path('about/', include('about.urls')),
    path('news/', include(('news.urls', 'news'), namespace='news')),
    path('consultant/', include('consultant.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),

    # 🔐 2FA — тимчасово відключено
    # path('account/', include('two_factor.urls')),

    path('contacts/', include('contacts.urls')),
    path('', include('lazysoft.dashboard_urls')),
    path('', include('core.urls')),

    prefix_default_language=True,
)

# Статика/медіа у DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
