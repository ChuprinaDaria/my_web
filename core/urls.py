from django.urls import path
from .views import home, WidgetMetricsAPIView, PublicDashboardAPIView

urlpatterns = [
    path('', home, name='home'),
    path('api/widget-metrics/', WidgetMetricsAPIView.as_view(), name='widget_metrics'),
    path('dashboard/public-api/', PublicDashboardAPIView.as_view(), name='public_dashboard_api'),
]
