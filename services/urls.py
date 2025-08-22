from django.urls import path
from .views import services_list, service_detail, services_api, services_by_tag

# services/urls.py
urlpatterns = [
    path('', services_list, name='services_list'),
    path('<slug:slug>/', service_detail, name='service_detail'),  
    path('tag/<str:tag_key>/', services_by_tag, name='services_by_tag'),  # 🆕
    path('api/services/', services_api, name='services_api'),              # 🆕# все інше як є
    
]
