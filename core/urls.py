from django.urls import path
from .views import home,   about_view
from django.urls import path, include

urlpatterns = [
    path('', home, name='home'),
    
    path("about/", about_view, name="about"),
    path('services/', include('services.urls')),


]
