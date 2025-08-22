# lazysoft/dashboard_views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .dashboard import LazySOFTDashboardAdmin
import logging

logger = logging.getLogger(__name__)

# Ініціалізуємо dashboard
dashboard_admin = LazySOFTDashboardAdmin()

@staff_member_required
@cache_page(1800)  # 30 хвилин кешу
def executive_dashboard_view(request):
    """📊 Головний executive dashboard"""
    period = request.GET.get('period', 'month')
    export_format = request.GET.get('export', None)
    
    try:
        data = dashboard_admin.get_executive_summary(period)
        
        # JSON експорт
        if export_format == 'json':
            return JsonResponse(data, safe=False)
        
        # HTML відображення
        context = {
            'title': 'LAZYSOFT Executive Dashboard',
            'data': data,
            'period': period,
            'periods': [
                ('today', 'Сьогодні'),
                ('week', 'Тиждень'), 
                ('month', 'Місяць'),
                ('quarter', 'Квартал')
            ]
        }
        
        return render(request, "dashboard/dashboard.html", context)
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@staff_member_required
def dashboard_api(request):
    """🔌 API для dashboard даних"""
    period = request.GET.get('period', 'week')
    component = request.GET.get('component', 'summary')
    
    data = dashboard_admin.get_executive_summary(period)
    
    if component == 'kpis':
        return JsonResponse(data.get('key_kpis', {}))
    elif component == 'health':
        return JsonResponse(data.get('health_check', {}))
    else:
        return JsonResponse(data)

def health_check(request):
    """🏥 Health check endpoint"""
    from .dashboard import system_health_check
    health = system_health_check()
    status_code = 200 if health['status'] != 'critical' else 503
    return JsonResponse(health, status=status_code)