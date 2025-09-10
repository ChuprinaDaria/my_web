from django.urls import path
from .views import services_list, service_detail

urlpatterns = [
    path('', services_list, name='services_list'),
    path('<slug:slug>/', service_detail, name='service_detail'),
]
