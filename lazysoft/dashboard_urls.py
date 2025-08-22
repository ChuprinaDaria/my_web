# lazysoft/dashboard_urls.py
from django.urls import path
from .dashboard_view import executive_dashboard_view, dashboard_api, health_check  # <- без 's'

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", executive_dashboard_view, name="executive"),
    path("dashboard/api/", dashboard_api, name="api"),
    path("dashboard/health/", health_check, name="health"),
]
