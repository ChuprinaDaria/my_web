import time
from django.core.cache import cache
from django.shortcuts import render
from django.http import HttpResponse
from news.services.telegram import send_security_alert
from core.services.cloudflare_api import auto_cloudflare_protection
import logging

logger = logging.getLogger('security')

class LinusSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Отримуємо інфо про запит
        ip = self.get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')
        path = request.path
        
        # Перевіряємо тригери
        attack_detected = self.check_for_attacks(request, ip, ua, path)
        
        if attack_detected:
            # Логуємо атаку
            self.log_attack(attack_detected, ip, ua, path)
            
            # Telegram alert
            send_security_alert(ip, attack_detected['type'], attack_detected['details'])
            
            # Cloudflare автоматичний захист
            auto_cloudflare_protection(ip, attack_detected['type'], attack_detected['details'])
            
            # Показуємо Linus! 🖕
            return render(request, 'security/linus.html', {
                'attack_type': attack_detected['type'],
                'ip_address': ip,
                'timestamp': time.time()
            })
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Отримуємо реальний IP клієнта"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_for_attacks(self, request, ip, ua, path):
        """Перевіряємо тригери для Linus"""
        
        # 1. Scanner Detection
        if self.is_scanner(ua):
            return {
                'type': 'scanner',
                'details': f'Scanner detected: {ua}'
            }
        
        # 2. Brute Force на /admin/
        if self.is_admin_bruteforce(request):
            return {
                'type': 'admin_bruteforce',
                'details': f'Admin brute force from {ip}'
            }
        
        # 3. API спам
        if self.is_api_spam(request):
            return {
                'type': 'api_spam',
                'details': f'API spam from {ip}'
            }
        
        # 4. Підозрілі POST дані (пропускаємо для admin)
        if not path.startswith('/admin/') and self.has_malicious_payload(request):
            return {
                'type': 'malicious_payload',
                'details': 'Malicious payload detected'
            }
        
        # 5. Fake bot User-Agents
        if self.is_fake_bot(request, ua):
            return {
                'type': 'fake_bot',
                'details': f'Fake bot detected: {ua}'
            }
        
        # 6. DDoS detection
        if self.is_ddos_attack(request, ip):
            return {
                'type': 'ddos',
                'details': f'DDoS attack detected from {ip}'
            }
        
        return None
    
    def is_scanner(self, ua):
        """Детекція сканерів - точні тригери"""
        scanners = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zap',
            'burpsuite', 'w3af', 'dirb', 'gobuster'
        ]
        return any(scanner in ua.lower() for scanner in scanners)
    
    
    def is_admin_bruteforce(self, request):
        """Детекція brute force на admin"""
        if not request.path.startswith('/admin/'):
            return False
        
        ip = self.get_client_ip(request)
        failed_count = cache.get(f'failed_admin_{ip}', 0)
        return failed_count > 5  # Після 5 спроб - Лінус!
    
    def is_api_spam(self, request):
        """Детекція API спаму"""
        if not request.path.startswith('/api/'):
            return False
            
        ip = self.get_client_ip(request)
        requests_count = cache.get(f'api_requests_{ip}', 0)
        return requests_count > 100  # 100 запитів за хвилину
    
    def has_malicious_payload(self, request):
        """Детекція зловмисних payload"""
        if request.method != 'POST':
            return False
            
        dangerous_patterns = [
            'union select', 'drop table', '<script>', 
            'javascript:', '../../etc/passwd'
        ]
        
        try:
            post_data = str(request.POST)
            if hasattr(request, 'body') and request.body:
                post_data += str(request.body)
        except Exception:
            post_data = str(request.POST)
        
        return any(pattern in post_data.lower() for pattern in dangerous_patterns)
    
    def is_fake_bot(self, request, ua):
        """Детекція фейкових ботів"""
        if 'googlebot' in ua.lower():
            ip = self.get_client_ip(request)
            # Перевіряємо чи IP справді з Google ranges
            return not self.is_google_ip(ip)
        return False
    
    def is_google_ip(self, ip):
        """Перевіряємо чи IP справді з Google"""
        # Спрощена перевірка - в реальності треба перевіряти всі Google IP ranges
        google_ranges = [
            '66.249.',  # Googlebot IP ranges
            '64.233.',
            '72.14.',
            '74.125.',
            '209.85.',
            '216.239.',
        ]
        return any(ip.startswith(range_prefix) for range_prefix in google_ranges)
    
    def is_ddos_attack(self, request, ip):
        """Детекція DDoS атак - більше 1000 запитів за хвилину"""
        cache_key = f'ddos_requests_{ip}'
        requests_count = cache.get(cache_key, 0)
        
        if requests_count >= 1000:  # 1000+ запитів за хвилину = DDoS
            return True
        
        # Збільшуємо лічильник
        cache.set(cache_key, requests_count + 1, 60)  # 1 хвилина
        return False
    
    def log_attack(self, attack, ip, ua, path):
        """Логуємо атаку"""
        logger.warning(f"🚨 LINUS BLOCKED: {attack['type']} from {ip} - {ua[:100]}")
        
        # Зберігаємо в файл
        try:
            with open('logs/security.log', 'a', encoding='utf-8') as f:
                f.write(f"{time.time()}: {attack['type']} from {ip} - {ua}\n")
        except Exception as e:
            logger.error(f"Failed to write security log: {e}")
