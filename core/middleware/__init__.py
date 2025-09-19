# Linus Security System™ Middleware Package
from .security_headers import SecurityHeadersMiddleware

class RequireOTPForAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/control/'):
            user = getattr(request, 'user', None)
            if user and user.is_authenticated and user.is_staff:
                is_verified = getattr(user, 'is_verified', None)
                if callable(is_verified):
                    verified = user.is_verified()
                else:
                    verified = False
                if not verified and not path.startswith('/control/login') and not path.startswith('/control/2fa/'):
                    from django.shortcuts import redirect
                    return redirect('admin_2fa_login')
        return self.get_response(request)