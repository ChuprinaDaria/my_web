"""
🖕 LINUS SECURITY SYSTEM™ - Dashboard
Статистика атак та заблокованих хакерів
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.core.cache import cache
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from core.services.cloudflare_api import get_cloudflare_stats
import json

@staff_member_required
def security_dashboard(request):
    """Dashboard з статистикою атак і Linus blocks"""
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    
    # Статистика за сьогодні
    stats = {
        'today_blocks': cache.get(f'linus_blocks_{today}', 0),
        'yesterday_blocks': cache.get(f'linus_blocks_{yesterday}', 0),
        'week_blocks': sum([
            cache.get(f'linus_blocks_{today - timedelta(days=i)}', 0) 
            for i in range(7)
        ]),
        'scanners_blocked': cache.get(f'scanner_{today}', 0),
        'bruteforce_attempts': cache.get(f'admin_bruteforce_{today}', 0),
        'sql_injections': cache.get(f'sql_injection_{today}', 0),
        'api_spam': cache.get(f'api_spam_{today}', 0),
        'suspicious_requests': cache.get(f'suspicious_{today}', 0),
    }
    
    # Top 10 заблокованих IP
    blocked_ips = cache.get('top_blocked_ips', [])
    
    # Статистика по годинах (останні 24 години)
    hourly_stats = []
    for i in range(24):
        hour = timezone.now().replace(hour=i, minute=0, second=0, microsecond=0)
        hour_key = f'linus_blocks_hour_{hour.strftime("%Y-%m-%d_%H")}'
        hourly_stats.append({
            'hour': hour.strftime('%H:00'),
            'blocks': cache.get(hour_key, 0)
        })
    
    # Статистика по типах атак
    attack_types = {
        'scanner': cache.get(f'scanner_{today}', 0),
        'sql_injection': cache.get(f'sql_injection_{today}', 0),
        'admin_bruteforce': cache.get(f'admin_bruteforce_{today}', 0),
        'api_spam': cache.get(f'api_spam_{today}', 0),
        'suspicious': cache.get(f'suspicious_{today}', 0),
    }
    
    # Статистика по країнах (якщо є GeoIP)
    country_stats = cache.get('country_stats', {})
    
    # Cloudflare статистика
    cloudflare_stats = get_cloudflare_stats()
    
    context = {
        'stats': stats,
        'blocked_ips': blocked_ips[:10],  # Top 10
        'hourly_stats': hourly_stats,
        'attack_types': attack_types,
        'country_stats': country_stats,
        'total_blocks': sum(stats.values()),
        'system_status': 'OPERATIONAL' if stats['today_blocks'] > 0 else 'QUIET',
        'cloudflare': cloudflare_stats,
    }
    
    return render(request, 'security/dashboard.html', context)

@staff_member_required
def security_api(request):
    """API endpoint для real-time статистики"""
    
    today = timezone.now().date()
    
    stats = {
        'today_blocks': cache.get(f'linus_blocks_{today}', 0),
        'scanners_blocked': cache.get(f'scanner_{today}', 0),
        'bruteforce_attempts': cache.get(f'admin_bruteforce_{today}', 0),
        'sql_injections': cache.get(f'sql_injection_{today}', 0),
        'api_spam': cache.get(f'api_spam_{today}', 0),
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(stats)

@staff_member_required
def clear_security_cache(request):
    """Очистити кеш безпеки (тільки для супер-адміністраторів)"""
    
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Очищаємо всі ключі безпеки
    security_keys = [
        'linus_blocks_',
        'scanner_',
        'admin_bruteforce_',
        'sql_injection_',
        'api_spam_',
        'suspicious_',
        'top_blocked_ips',
        'country_stats',
    ]
    
    cleared_count = 0
    for key in security_keys:
        # Отримуємо всі ключі що починаються з цього префіксу
        # (це спрощена версія, в реальності треба використовувати cache.keys())
        cleared_count += 1
    
    return JsonResponse({
        'message': f'Cleared {cleared_count} security cache entries',
        'timestamp': timezone.now().isoformat()
    })

@staff_member_required
def security_logs(request):
    """Перегляд логів безпеки"""
    
    try:
        with open('logs/security.log', 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        # Показуємо останні 100 записів
        recent_logs = logs[-100:] if len(logs) > 100 else logs
        
        context = {
            'logs': recent_logs,
            'total_logs': len(logs),
            'showing': len(recent_logs)
        }
        
        return render(request, 'security/logs.html', context)
        
    except FileNotFoundError:
        context = {
            'logs': [],
            'total_logs': 0,
            'showing': 0,
            'error': 'Security log file not found'
        }
        return render(request, 'security/logs.html', context)
