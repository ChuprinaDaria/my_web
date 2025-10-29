from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('contracts/<int:contract_id>/generate-pdf/', views.generate_contract_pdf, name='generate_contract_pdf'),
]

