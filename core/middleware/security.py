import time
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.http import HttpResponse
from news.services.telegram import send_security_alert
from core.services.cloudflare_api import auto_cloudflare_protection
import logging

logger = logging.getLogger('security')


class WWWRedirectMiddleware:
    """Редірект з www на non-www версію (канонічна)"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()
        if host.startswith('www.'):
            # Редірект на non-www версію
            new_host = host[4:]  # Видаляємо 'www.'
            new_url = f"{request.scheme}://{new_host}{request.get_full_path()}"
            return redirect(new_url, permanent=True)
        return self.get_response(request)

class LinusSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        ip = self.get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')
        path = request.path
        
        attack_detected = self.check_for_attacks(request, ip, ua, path)
        
        if attack_detected:
            self.log_attack(attack_detected, ip, ua, path)
            send_security_alert(ip, attack_detected['type'], attack_detected['details'])
            auto_cloudflare_protection(ip, attack_detected['type'], attack_detected['details'])
            return render(request, 'security/linus.html', {
                'attack_type': attack_detected['type'],
                'ip_address': ip,
                'timestamp': time.time()
            })
        
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def check_for_attacks(self, request, ip, ua, path):
        if self.is_scanner(ua):
            return {'type': 'scanner', 'details': f'Scanner detected: {ua}'}
        if self.is_admin_bruteforce(request):
            return {'type': 'admin_bruteforce', 'details': f'Admin brute force from {ip}'}
        if self.is_api_spam(request):
            return {'type': 'api_spam', 'details': f'API spam from {ip}'}
        if not path.startswith('/admin/') and self.has_malicious_payload(request):
            return {'type': 'malicious_payload', 'details': 'Malicious payload detected'}
        if self.is_fake_bot(request, ua):
            return {'type': 'fake_bot', 'details': f'Fake bot detected: {ua}'}
        if self.is_ddos_attack(request, ip):
            return {'type': 'ddos', 'details': f'DDoS attack detected from {ip}'}
        return None

    def is_scanner(self, ua):
        scanners = ['sqlmap', 'nikto', 'nmap', 'masscan', 'zap', 'burpsuite', 'w3af', 'dirb', 'gobuster']
        return any(scanner in ua.lower() for scanner in scanners)

    def is_admin_bruteforce(self, request):
        if not request.path.startswith('/admin/'):
            return False
        ip = self.get_client_ip(request)
        failed_count = cache.get(f'failed_admin_{ip}', 0)
        return failed_count > 5

    def is_api_spam(self, request):
        if not request.path.startswith('/api/'):
            return False
        ip = self.get_client_ip(request)
        requests_count = cache.get(f'api_requests_{ip}', 0)
        return requests_count > 100

    def has_malicious_payload(self, request):
        if request.method != 'POST':
            return False
        dangerous_patterns = ['union select', 'drop table', '<script>', 'javascript:', '../../etc/passwd']
        try:
            post_data = str(request.POST)
            if hasattr(request, 'body') and request.body:
                post_data += str(request.body)
        except Exception:
            post_data = str(request.POST)
        return any(pattern in post_data.lower() for pattern in dangerous_patterns)

    def is_fake_bot(self, request, ua):
        """
        Детекція фейкових ботів.

        ВАЖЛИВО: для Googlebot ми НІЧОГО не блокуємо, тільки логуємо підозрілі IP,
        щоб ніколи випадково не відрізати справжнього Googlebot / індексацію.
        """
        if 'googlebot' in ua.lower():
            ip = self.get_client_ip(request)
            if not self.is_google_ip(ip):
                logger.warning(f"Suspicious Googlebot UA from {ip}: {ua[:200]}")
            # НІКОЛИ не блокуємо Googlebot – навіть якщо IP виглядає підозрілим
            return False
        return False

    def is_google_ip(self, ip):
        """Перевіряємо чи IP справді з Google через reverse DNS"""
        import socket

        try:
            # Спочатку швидка перевірка IPv6
            if ':' in ip:
                google_ipv6_ranges = [
                    '2001:4860:',  # Основний діапазон Google IPv6
                    '2404:6800:',  # Google Азія
                    '2607:f8b0:',  # Google США
                    '2800:3f0:',   # Google Латинська Америка
                    '2a00:1450:',  # Google Європа
                    '2c0f:fb50:',  # Google Африка
                ]
                ip_normalized = ip.lower().replace(':0000:', ':0:').replace(':::', '::')
                if any(ip_normalized.startswith(prefix.lower()) for prefix in google_ipv6_ranges):
                    return True

            # Reverse DNS lookup - найнадійніший метод для Google
            # Google каже: перевіряйте через reverse DNS lookup
            hostname, _, _ = socket.gethostbyaddr(ip)

            # Перевіряємо чи hostname закінчується на .googlebot.com або .google.com
            if hostname.endswith('.googlebot.com') or hostname.endswith('.google.com'):
                # Додаткова перевірка: forward DNS lookup
                forward_ip = socket.gethostbyname(hostname)
                return forward_ip == ip

            return False

        except (socket.herror, socket.gaierror, socket.timeout):
            # Якщо reverse DNS не працює, fallback на IP ranges
            # Але це небезпечно, тому логуємо
            logger.info(f"Reverse DNS lookup failed for {ip}, using IP range fallback")

            # Fallback: базові Google IP ranges
            # УВАГА: Це НЕ 100% надійно, краще використовувати reverse DNS
            google_ranges = [
                '66.249.',   # Основні Googlebot IP
                '64.233.',   # Google infrastructure
                '72.14.',    # Google services
                '74.125.',   # Google services
                '209.85.',   # Google services
                '216.239.',  # Google services
                '192.178.',  # Google Cloud (verified bots використовують)
            ]
            return any(ip.startswith(range_prefix) for range_prefix in google_ranges)

    def is_ddos_attack(self, request, ip):
        cache_key = f'ddos_requests_{ip}'
        requests_count = cache.get(cache_key, 0)
        if requests_count >= 1000:
            return True
        cache.set(cache_key, requests_count + 1, 60)
        return False

    def log_attack(self, attack, ip, ua, path):
        logger.warning(f"🚨 LINUS BLOCKED: {attack['type']} from {ip} - {ua[:100]}")
        try:
            with open('logs/security.log', 'a', encoding='utf-8') as f:
                f.write(f"{time.time()}: {attack['type']} from {ip} - {ua}\n")
        except Exception as e:
            logger.error(f"Failed to write security log: {e}")

import time as _time
import jwt
from django.conf import settings
from django.shortcuts import redirect


class AdminJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ''
        normalized_path = self._strip_language_prefix(path)
        is_logout = path.endswith('/logout/') or normalized_path == '/control/logout/' or normalized_path == '/admin/logout/'
        if normalized_path.startswith('/control/') and not normalized_path.startswith('/control/login') and not normalized_path.startswith('/control/2fa/') and not is_logout:
            token = request.COOKIES.get(getattr(settings, 'ADMIN_JWT_COOKIE_NAME', 'admin_jwt'))
            if not token:
                return redirect('admin_2fa_login')
            try:
                payload = jwt.decode(
                    token,
                    getattr(settings, 'ADMIN_JWT_SECRET', settings.SECRET_KEY),
                    algorithms=[getattr(settings, 'ADMIN_JWT_ALG', 'HS256')]
                )
                exp = int(payload.get('exp', 0))
                if exp <= int(_time.time()):
                    resp = redirect('admin_2fa_login')
                    resp.delete_cookie(getattr(settings, 'ADMIN_JWT_COOKIE_NAME', 'admin_jwt'))
                    return resp
            except Exception:
                resp = redirect('admin_2fa_login')
                resp.delete_cookie(getattr(settings, 'ADMIN_JWT_COOKIE_NAME', 'admin_jwt'))
                return resp
        response = self.get_response(request)
        if is_logout:
            response.delete_cookie(getattr(settings, 'ADMIN_JWT_COOKIE_NAME', 'admin_jwt'))
        return response
    
    def _strip_language_prefix(self, path):
        languages = [code for code, _ in getattr(settings, 'LANGUAGES', [])]
        for code in languages:
            prefix = f'/{code}/'
            if path.startswith(prefix):
                return '/' + path[len(prefix):]
        return path
    
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
        """Детекція фейкових ботів.

        Для Googlebot діє та сама політика: нічого не блокуємо, тільки логуємо,
        щоб не ризикувати SEO / індексацією.
        """
        if 'googlebot' in ua.lower():
            ip = self.get_client_ip(request)
            if not self.is_google_ip(ip):
                logger.warning(f"Suspicious Googlebot UA (AdminJWT) from {ip}: {ua[:200]}")
            return False
        return False

    def is_google_ip(self, ip):
        """Перевіряємо чи IP справді з Google через reverse DNS (duplicate method - should use the one above)"""
        import socket

        try:
            # Спочатку швидка перевірка IPv6
            if ':' in ip:
                google_ipv6_ranges = [
                    '2001:4860:',  # Основний діапазон Google IPv6
                    '2404:6800:',  # Google Азія
                    '2607:f8b0:',  # Google США
                    '2800:3f0:',   # Google Латинська Америка
                    '2a00:1450:',  # Google Європа
                    '2c0f:fb50:',  # Google Африка
                ]
                ip_normalized = ip.lower().replace(':0000:', ':0:').replace(':::', '::')
                if any(ip_normalized.startswith(prefix.lower()) for prefix in google_ipv6_ranges):
                    return True

            # Reverse DNS lookup - найнадійніший метод для Google
            hostname, _, _ = socket.gethostbyaddr(ip)

            # Перевіряємо чи hostname закінчується на .googlebot.com або .google.com
            if hostname.endswith('.googlebot.com') or hostname.endswith('.google.com'):
                # Додаткова перевірка: forward DNS lookup
                forward_ip = socket.gethostbyname(hostname)
                return forward_ip == ip

            return False

        except (socket.herror, socket.gaierror, socket.timeout):
            # Fallback на IP ranges якщо DNS не працює
            google_ranges = [
                '66.249.',   # Основні Googlebot IP
                '64.233.',   # Google infrastructure
                '72.14.',    # Google services
                '74.125.',   # Google services
                '209.85.',   # Google services
                '216.239.',  # Google services
                '192.178.',  # Google Cloud (verified bots використовують)
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
