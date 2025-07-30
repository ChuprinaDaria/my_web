from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Якщо потрібно: інші URL, які не залежать від мови
]
print("🧠 i18n_patterns ACTUALLY LOADED")

# Головна магія:
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # ← ось він, твій `home` і `projects/`
    prefix_default_language=False,  # Щоб /uk/ не дублювався для default lang
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
