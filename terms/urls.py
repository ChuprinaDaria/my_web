from django.urls import path
from . import views

app_name = 'terms'

urlpatterns = [
    path('<slug:slug>/', views.static_page_view, name='static_page'),
]