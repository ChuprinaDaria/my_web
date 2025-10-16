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
        if 'googlebot' in ua.lower():
            ip = self.get_client_ip(request)
            return not self.is_google_ip(ip)
        return False

    def is_google_ip(self, ip):
        google_ranges = ['66.249.', '64.233.', '72.14.', '74.125.', '209.85.', '216.239.']
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
        """Детекція фейкових ботів"""
        if 'googlebot' in ua.lower():
            ip = self.get_client_ip(request)
            # Перевіряємо чи IP справді з Google ranges
            return not self.is_google_ip(ip)
        return False
    
    def is_google_ip(self, ip):
        """Перевіряємо чи IP справді з Google"""
        # Розширені Google IP ranges для кращої підтримки Google ботів
        google_ranges = [
            '66.249.',  # Googlebot IP ranges
            '64.233.',
            '72.14.',
            '74.125.',
            '209.85.',
            '216.239.',
            '192.178.',  # Додаємо діапазон з заблокованого IP
            '34.64.',
            '34.65.',
            '34.66.',
            '34.67.',
            '34.68.',
            '34.69.',
            '34.70.',
            '34.71.',
            '34.72.',
            '34.73.',
            '34.74.',
            '34.75.',
            '34.76.',
            '34.77.',
            '34.78.',
            '34.79.',
            '34.80.',
            '34.81.',
            '34.82.',
            '34.83.',
            '34.84.',
            '34.85.',
            '34.86.',
            '34.87.',
            '34.88.',
            '34.89.',
            '34.90.',
            '34.91.',
            '34.92.',
            '34.93.',
            '34.94.',
            '34.95.',
            '34.96.',
            '34.97.',
            '34.98.',
            '34.99.',
            '34.100.',
            '34.101.',
            '34.102.',
            '34.103.',
            '34.104.',
            '34.105.',
            '34.106.',
            '34.107.',
            '34.108.',
            '34.109.',
            '34.110.',
            '34.111.',
            '34.112.',
            '34.113.',
            '34.114.',
            '34.115.',
            '34.116.',
            '34.117.',
            '34.118.',
            '34.119.',
            '34.120.',
            '34.121.',
            '34.122.',
            '34.123.',
            '34.124.',
            '34.125.',
            '34.126.',
            '34.127.',
            '34.128.',
            '34.129.',
            '34.130.',
            '34.131.',
            '34.132.',
            '34.133.',
            '34.134.',
            '34.135.',
            '34.136.',
            '34.137.',
            '34.138.',
            '34.139.',
            '34.140.',
            '34.141.',
            '34.142.',
            '34.143.',
            '34.144.',
            '34.145.',
            '34.146.',
            '34.147.',
            '34.148.',
            '34.149.',
            '34.150.',
            '34.151.',
            '34.152.',
            '34.153.',
            '34.154.',
            '34.155.',
            '34.156.',
            '34.157.',
            '34.158.',
            '34.159.',
            '34.160.',
            '34.161.',
            '34.162.',
            '34.163.',
            '34.164.',
            '34.165.',
            '34.166.',
            '34.167.',
            '34.168.',
            '34.169.',
            '34.170.',
            '34.171.',
            '34.172.',
            '34.173.',
            '34.174.',
            '34.175.',
            '34.176.',
            '34.177.',
            '34.178.',
            '34.179.',
            '34.180.',
            '34.181.',
            '34.182.',
            '34.183.',
            '34.184.',
            '34.185.',
            '34.186.',
            '34.187.',
            '34.188.',
            '34.189.',
            '34.190.',
            '34.191.',
            '34.192.',
            '34.193.',
            '34.194.',
            '34.195.',
            '34.196.',
            '34.197.',
            '34.198.',
            '34.199.',
            '34.200.',
            '34.201.',
            '34.202.',
            '34.203.',
            '34.204.',
            '34.205.',
            '34.206.',
            '34.207.',
            '34.208.',
            '34.209.',
            '34.210.',
            '34.211.',
            '34.212.',
            '34.213.',
            '34.214.',
            '34.215.',
            '34.216.',
            '34.217.',
            '34.218.',
            '34.219.',
            '34.220.',
            '34.221.',
            '34.222.',
            '34.223.',
            '34.224.',
            '34.225.',
            '34.226.',
            '34.227.',
            '34.228.',
            '34.229.',
            '34.230.',
            '34.231.',
            '34.232.',
            '34.233.',
            '34.234.',
            '34.235.',
            '34.236.',
            '34.237.',
            '34.238.',
            '34.239.',
            '34.240.',
            '34.241.',
            '34.242.',
            '34.243.',
            '34.244.',
            '34.245.',
            '34.246.',
            '34.247.',
            '34.248.',
            '34.249.',
            '34.250.',
            '34.251.',
            '34.252.',
            '34.253.',
            '34.254.',
            '34.255.',
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
