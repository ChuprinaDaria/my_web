import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('security')

class LighthouseCompatibleSecurityMiddleware(MiddlewareMixin):
    """
    Легкий security middleware, сумісний з Lighthouse
    """
    
    def process_response(self, request, response):
        # Базові security headers без блокування Lighthouse
        
        # X-Content-Type-Options - безпечно
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options - безпечно
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Referrer-Policy - безпечно
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy - безпечно
        response['Permissions-Policy'] = (
            'accelerometer=(), camera=(), geolocation=(), gyroscope=(), '
            'magnetometer=(), microphone=(), payment=(), usb=()'
        )
        
        # COOP - тільки для HTTPS або localhost
        if request.is_secure() or request.get_host().startswith('localhost') or request.get_host().startswith('127.0.0.1'):
            response['Cross-Origin-Opener-Policy'] = 'same-origin'
            logger.debug(f"COOP header added for {request.get_host()}")
        else:
            logger.debug(f"COOP header skipped for {request.get_host()} (not secure context)")
        
        # CORP - безпечно
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # Базовий CSP без блокування
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' https:;"
        )
        
        # HSTS тільки для production
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000'
        
        return response
