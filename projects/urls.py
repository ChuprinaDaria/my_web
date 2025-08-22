from django.urls import path
from .views import (
    projects_list,
    project_detail,
    project_contact_submit,
    projects_api, projects_by_tag,
)

urlpatterns = [
    path('', projects_list, name='projects'),
    path('<slug:slug>/', project_detail, name='project_detail'),
    path('<slug:slug>/contact/', project_contact_submit, name='project_contact_submit'),
    path('api/projects/', projects_api, name='projects_api'),
    path('tag/<str:tag_key>/', projects_by_tag, name='projects_by_tag'), 
]