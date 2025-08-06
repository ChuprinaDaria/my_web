from django.urls import path
from .views import services_list, service_detail, faq_page

# services/urls.py
urlpatterns = [
    path('', services_list, name='services_list'),
    path('<slug:slug>/', service_detail, name='service_detail'),  # все інше як є
    
]
