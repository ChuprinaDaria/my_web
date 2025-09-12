from django.urls import path
from .views import home, robots_txt, WidgetMetricsAPIView, PublicDashboardAPIView

urlpatterns = [
    path('', home, name='home'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('api/widget-metrics/', WidgetMetricsAPIView.as_view(), name='widget_metrics'),
    path('dashboard/public-api/', PublicDashboardAPIView.as_view(), name='public_dashboard_api'),
]
