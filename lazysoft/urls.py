from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from services.views import faq_page

print("🧠 i18n_patterns ACTUALLY LOADED")

urlpatterns = []

# 🔤 URL з мовними префіксами
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('services/', include('services.urls')),
    path('projects/', include('projects.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('faq/', faq_page, name='faq_page'),
    # порядок важливий: faq передається напряму
    # services включає решту
    # core — це головна, about і т.п.
    # ckeditor — для медіа редактора
    # admin — класика
    # всі ці шляхи будуть працювати як /uk/... /pl/... /en/...
    # нижче задається параметр, щоб /en не було префіксом по замовчуванню
    prefix_default_language=True
)

# 🧪 Статика та медіа під час розробки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
