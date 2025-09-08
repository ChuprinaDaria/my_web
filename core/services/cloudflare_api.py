"""
☁️ CLOUDFLARE API INTEGRATION
Автоматичне управління захистом через Cloudflare API
"""

import requests
import logging
from django.conf import settings
from typing import Dict, List, Optional

logger = logging.getLogger('security')

class CloudflareAPI:
    """Cloudflare API клієнт для управління захистом"""
    
    def __init__(self):
        self.api_token = getattr(settings, 'CLOUDFLARE_API_TOKEN', None)
        self.zone_id = getattr(settings, 'CLOUDFLARE_ZONE_ID', None)
        self.email = getattr(settings, 'CLOUDFLARE_EMAIL', None)
        
        if not all([self.api_token, self.zone_id]):
            logger.warning("Cloudflare API credentials not configured")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Робимо API запит до Cloudflare"""
        if not self.api_token or not self.zone_id:
            return None
            
        url = f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Cloudflare API request failed: {e}")
            return None
    
    def enable_under_attack_mode(self) -> bool:
        """Включаємо Under Attack Mode"""
        data = {
            "value": "under_attack"
        }
        
        result = self._make_request('PATCH', 'settings/security_level', data)
        if result and result.get('success'):
            logger.warning("🚨 UNDER ATTACK MODE ENABLED via Cloudflare API")
            return True
        return False
    
    def disable_under_attack_mode(self) -> bool:
        """Вимикаємо Under Attack Mode"""
        data = {
            "value": "high"
        }
        
        result = self._make_request('PATCH', 'settings/security_level', data)
        if result and result.get('success'):
            logger.info("✅ Under Attack Mode disabled")
            return True
        return False
    
    def block_ip(self, ip_address: str, reason: str = "Linus Security Block") -> bool:
        """Блокуємо IP через Cloudflare"""
        data = {
            "mode": "block",
            "configuration": {
                "target": "ip",
                "value": ip_address
            },
            "notes": f"Linus Security: {reason}"
        }
        
        result = self._make_request('POST', 'firewall/access_rules/rules', data)
        if result and result.get('success'):
            logger.warning(f"🚫 IP {ip_address} blocked via Cloudflare: {reason}")
            return True
        return False
    
    def challenge_ip(self, ip_address: str, reason: str = "Linus Security Challenge") -> bool:
        """Ставимо Challenge для IP"""
        data = {
            "mode": "challenge",
            "configuration": {
                "target": "ip",
                "value": ip_address
            },
            "notes": f"Linus Security: {reason}"
        }
        
        result = self._make_request('POST', 'firewall/access_rules/rules', data)
        if result and result.get('success'):
            logger.warning(f"🤖 IP {ip_address} challenged via Cloudflare: {reason}")
            return True
        return False
    
    def get_zone_analytics(self) -> Optional[Dict]:
        """Отримуємо аналітику зони"""
        result = self._make_request('GET', 'analytics/dashboard')
        return result
    
    def get_security_events(self) -> Optional[Dict]:
        """Отримуємо security events"""
        result = self._make_request('GET', 'security/events')
        return result
    
    def is_under_attack(self) -> bool:
        """Перевіряємо чи включений Under Attack Mode"""
        result = self._make_request('GET', 'settings/security_level')
        if result and result.get('success'):
            return result.get('result', {}).get('value') == 'under_attack'
        return False
    
    def get_rate_limit_rules(self) -> Optional[List[Dict]]:
        """Отримуємо правила rate limiting"""
        result = self._make_request('GET', 'rate_limits')
        if result and result.get('success'):
            return result.get('result', [])
        return None
    
    def create_rate_limit_rule(self, ip_address: str, requests_per_minute: int = 10) -> bool:
        """Створюємо rate limit правило для IP"""
        data = {
            "match": {
                "request": {
                    "urls": ["*"],
                    "schemes": ["HTTP", "HTTPS"],
                    "methods": ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
                },
                "client_ip": {
                    "ip": ip_address
                }
            },
            "action": {
                "mode": "simulate",
                "timeout": 60,
                "response": {
                    "status_code": 429,
                    "body": "Rate limit exceeded. Linus Security System™ is watching you! 🖕"
                }
            },
            "threshold": requests_per_minute,
            "period": 60,
            "disabled": False
        }
        
        result = self._make_request('POST', 'rate_limits', data)
        if result and result.get('success'):
            logger.warning(f"⏱️ Rate limit rule created for {ip_address}: {requests_per_minute} req/min")
            return True
        return False


def auto_cloudflare_protection(ip_address: str, attack_type: str, details: str = ""):
    """Автоматично включаємо захист Cloudflare на основі типу атаки"""
    
    if not getattr(settings, 'CLOUDFLARE_API_TOKEN', None):
        logger.debug("Cloudflare API not configured - skipping auto protection")
        return
    
    cf = CloudflareAPI()
    
    try:
        if attack_type == 'ddos':
            # DDoS атака - включаємо Under Attack Mode
            cf.enable_under_attack_mode()
            logger.critical(f"🚨 DDoS DETECTED - Under Attack Mode enabled for {ip_address}")
            
        elif attack_type == 'mass_scanner':
            # Масове сканування - блокуємо IP
            cf.block_ip(ip_address, f"Mass scanner: {details}")
            
        elif attack_type == 'admin_bruteforce':
            # Brute force на admin - ставимо challenge
            cf.challenge_ip(ip_address, f"Admin brute force: {details}")
            
        elif attack_type == 'api_spam':
            # API спам - створюємо rate limit
            cf.create_rate_limit_rule(ip_address, 10)  # 10 запитів за хвилину
            
        elif attack_type in ['scanner', 'malicious_payload', 'fake_bot']:
            # Інші атаки - блокуємо IP
            cf.block_ip(ip_address, f"{attack_type}: {details}")
            
    except Exception as e:
        logger.error(f"Failed to apply Cloudflare protection: {e}")


def get_cloudflare_stats() -> Dict:
    """Отримуємо статистику Cloudflare"""
    cf = CloudflareAPI()
    
    stats = {
        'under_attack_mode': cf.is_under_attack(),
        'zone_analytics': cf.get_zone_analytics(),
        'security_events': cf.get_security_events(),
        'rate_limits': cf.get_rate_limit_rules()
    }
    
    return stats
