# contacts/urls.py - ЗМІНИ ЦЕ:
from django.urls import path
from . import views

app_name = 'contacts'  # 👈 ЗМІНИ з 'contacts_app' на 'contacts'

urlpatterns = [
    # Сторінка контактів
    path('', views.ContactView.as_view(), name='contact_page'),
    
    # API для форми
    path('submit/', views.submit_contact_form, name='submit_form'),
]