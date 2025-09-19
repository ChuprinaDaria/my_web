"""
🍪 Cookie Consent Middleware
Простий middleware для обробки cookie consent
"""


class CookieConsentMiddleware:
    """
    Middleware для роботи з cookie consent
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Додаємо інформацію про cookie consent до request
        request.cookie_consent = self.get_cookie_consent_status(request)

        response = self.get_response(request)

        return response

    def get_cookie_consent_status(self, request):
        """
        Отримуємо статус згоди на cookies
        """
        consent_cookie = request.COOKIES.get('cookie_consent', None)

        return {
            'has_consent': consent_cookie in ['accepted', 'declined'],
            'is_accepted': consent_cookie == 'accepted',
            'is_declined': consent_cookie == 'declined',
            'show_banner': consent_cookie is None,
        }


