from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from services.views import faq_page

# 📰 Імпортуємо sitemaps для SEO
try:
    from news.views import NewsSitemap, NewsCategorySitemap
    SITEMAPS_AVAILABLE = True
except ImportError:
    SITEMAPS_AVAILABLE = False
    print("⚠️ News sitemaps not available - run migrations first")

print("🧠 i18n_patterns ACTUALLY LOADED")

urlpatterns = []

# 🗺️ Sitemap для SEO (без мовних префіксів)
if SITEMAPS_AVAILABLE:
    sitemaps = {
        'news': NewsSitemap,
        'news_categories': NewsCategorySitemap,
    }
    
    urlpatterns += [
        path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, 
             name='django.contrib.sitemaps.views.sitemap'),
        path('sitemap-news.xml', sitemap, {'sitemaps': {'news': NewsSitemap}}, 
             name='news_sitemap'),
        path('sitemap-categories.xml', sitemap, {'sitemaps': {'categories': NewsCategorySitemap}}, 
             name='categories_sitemap'),
    ]

# 📰 RSS фід для новин (без мовних префіксів)
urlpatterns += [
    
    path('robots.txt', include('core.urls')),    # robots.txt якщо потрібно
]

# 🔤 URL з мовними префіксами
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('services/', include('services.urls')),
    path('projects/', include('projects.urls')),
    path('', include('lazysoft.dashboard_urls')),
    # 📰 НОВИНИ - додаємо новинну систему
    path('news/', include(('news.urls', 'news'), namespace='news')),
    
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('faq/', faq_page, name='faq_page'),
    
    path('contacts/', include('contacts.urls')),
    # services — послуги та FAQ
    # projects — портфоліо проєктів
    # news — новинна система з AI обробкою 📰🤖
    # ckeditor — для медіа редактора
    # faq — окрема сторінка FAQ
    # всі ці шляхи будуть працювати як /uk/news/ /pl/news/ /en/news/
    prefix_default_language=True
)

# 🧪 Статика та медіа під час розробки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 🎯 SEO URLs для новин (додаткові маршрути)
# Ці URL будуть доступні як:
# /uk/news/ - список новин українською
# /en/news/ - список новин англійською  
# /pl/news/ - список новин польською
# /uk/news/category/ai/ - AI новини українською
# /uk/news/article/uuid-here/ - детальна стаття
# /news/rss.xml - RSS фід (без мовного префіксу)
# /sitemap.xml - XML sitemap для пошукових систем