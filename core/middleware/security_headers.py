from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger('security')

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Додаємо логування для діагностики
        logger.info(f"SecurityHeadersMiddleware: Processing {request.path}")
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://www.googletagmanager.com "
            "https://www.google-analytics.com "
            "https://unpkg.com "
            "https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com; "
            "font-src 'self' "
            "https://fonts.gstatic.com; "
            "img-src 'self' data: blob: "
            "https://images.unsplash.com "
            "https://cdn.pixabay.com "
            "https://images.pexels.com "
            "https://www.gstatic.com; "
            "connect-src 'self' "
            "https://www.google-analytics.com "
            "https://analytics.google.com "
            "https://region1.google-analytics.com "
            "https://unpkg.com; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )
        
        response['Content-Security-Policy'] = csp_policy
        logger.info(f"Added CSP header: {csp_policy[:50]}...")
        
        # HSTS Header
        # НЕ додаємо HSTS в DEBUG режимі, щоб уникнути проблем з HTTP
        if not settings.DEBUG:
            # В production - повний HSTS
            hsts_value = 'max-age=31536000; includeSubDomains; preload'
            response['Strict-Transport-Security'] = hsts_value
            logger.info(f"Added HSTS header (PRODUCTION): {hsts_value}")
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'interest-cohort=(), payment=(), usb=()'
        )
        
        # Cross-Origin Embedder Policy
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        
        # Cross-Origin Opener Policy
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        
        # Cross-Origin Resource Policy
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        logger.info(f"Security headers applied to {request.path}")
        
        return response
