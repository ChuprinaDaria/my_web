from django.urls import path
from .views import services_list, service_detail, faq_list

urlpatterns = [
    path('', services_list, name='services_list'),
    path('faq/', faq_list, name='faq_list'),
    path('<slug:slug>/', service_detail, name='service_detail'),
]
