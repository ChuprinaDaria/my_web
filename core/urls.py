from django.urls import path
from .views import home,  projects, about_view

urlpatterns = [
    path('', home, name='home'),
    path('projects/', projects, name='projects'),
    path("about/", about_view, name="about")

]
