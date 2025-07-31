from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language

# URL без языкового префикса
urlpatterns = [
    path('i18n/setlang/', set_language, name='set_language'),
]

print("🧠 i18n_patterns ACTUALLY LOADED")

# URL с языковыми префиксами
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    prefix_default_language=False,  # Важно для работы без префикса
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])