from django.urls import path
from .views import blog_list, blog_detail, rate_post

app_name = "blog"

urlpatterns = [
    path("", blog_list, name="blog_list"),
    path("<slug:slug>/", blog_detail, name="blog_detail"),
    path("<slug:slug>/rate/", rate_post, name="rate_post"),
]


