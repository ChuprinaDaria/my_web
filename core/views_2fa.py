# core/views_2fa.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.conf import settings
import jwt
import time
from django.views.generic import View
from django_otp.decorators import otp_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticToken
from django_otp.util import random_hex
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64


class TwoFactorLoginView(View):
    """2FA Login View для адмін панелі"""
    template_name = 'admin/2fa_login.html'
    
    def get(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'is_verified') and request.user.is_verified():
            return redirect('/control/')
        context = {}
        # Якщо явно не крок з токеном – очищаємо можливу застарілу сесію
        if request.GET.get('step') == 'token' and request.session.get('2fa_user_id'):
            context['show_token_form'] = True
        else:
            try:
                del request.session['2fa_user_id']
            except KeyError:
                pass
        return render(request, self.template_name, context)
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        token = request.POST.get('token')
        next_url = request.POST.get('next') or request.GET.get('next') or '/admin/'
        
        # Крок 2: перевірка токена без повторного введення логіна/пароля
        if token and request.session.get('2fa_user_id'):
            user_id = request.session.get('2fa_user_id')
            try:
                user = get_user_model().objects.get(id=user_id)
            except get_user_model().DoesNotExist:
                messages.error(request, 'Сесія 2FA втрачена. Увійдіть знову.')
                return render(request, self.template_name)
            if self.verify_token(user, token):
                backend = request.session.get('2fa_backend') or 'django.contrib.auth.backends.ModelBackend'
                login(request, user, backend=backend)
                try:
                    payload = {
                        'uid': user.id,
                        'is_staff': True,
                        'exp': int(time.time()) + int(getattr(settings, 'ADMIN_JWT_TTL_MIN', 30)) * 60
                    }
                    token = jwt.encode(payload, getattr(settings, 'ADMIN_JWT_SECRET', settings.SECRET_KEY), algorithm=getattr(settings, 'ADMIN_JWT_ALG', 'HS256'))
                except Exception:
                    token = None
                try:
                    del request.session['2fa_user_id']
                except KeyError:
                    pass
                try:
                    del request.session['2fa_backend']
                except KeyError:
                    pass
                resp = redirect(next_url or '/control/')
                if token:
                    resp.set_cookie(
                        getattr(settings, 'ADMIN_JWT_COOKIE_NAME', 'admin_jwt'),
                        token,
                        max_age=int(getattr(settings, 'ADMIN_JWT_TTL_MIN', 30)) * 60,
                        secure=bool(getattr(settings, 'ADMIN_JWT_COOKIE_SECURE', not settings.DEBUG)),
                        httponly=True,
                        samesite=getattr(settings, 'ADMIN_JWT_COOKIE_SAMESITE', 'Lax')
                    )
                return resp
            messages.error(request, 'Невірний 2FA токен')
            return render(request, self.template_name, {'show_token_form': True, 'next': next_url})

        if token and not request.session.get('2fa_user_id'):
            messages.error(request, 'Спочатку введіть логін і пароль')
            return render(request, self.template_name)

        # Крок 1: перевірка логіна/пароля
        if not all([username, password]):
            messages.error(request, 'Будь ласка, заповніть всі поля')
            return render(request, self.template_name)
        
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, 'Невірний логін або пароль')
            return render(request, self.template_name)
        
        if not user.is_staff:
            messages.error(request, 'Доступ заборонено')
            return render(request, self.template_name)
        
        # Перевіряємо 2FA токен
        if token:
            if self.verify_token(user, token):
                backend = getattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend')
                login(request, user, backend=backend)
                try:
                    payload = {
                        'uid': user.id,
                        'is_staff': True,
                        'exp': int(time.time()) + int(getattr(settings, 'ADMIN_JWT_TTL_MIN', 30)) * 60
                    }
                    token = jwt.encode(payload, getattr(settings, 'ADMIN_JWT_SECRET', settings.SECRET_KEY), algorithm=getattr(settings, 'ADMIN_JWT_ALG', 'HS256'))
                except Exception:
                    token = None
                try:
                    del request.session['2fa_user_id']
                except KeyError:
                    pass
                resp = redirect(next_url or '/control/')
                if token:
                    resp.set_cookie(
                        getattr(settings, 'ADMIN_JWT_COOKIE_NAME', 'admin_jwt'),
                        token,
                        max_age=int(getattr(settings, 'ADMIN_JWT_TTL_MIN', 30)) * 60,
                        secure=bool(getattr(settings, 'ADMIN_JWT_COOKIE_SECURE', not settings.DEBUG)),
                        httponly=True,
                        samesite=getattr(settings, 'ADMIN_JWT_COOKIE_SAMESITE', 'Lax')
                    )
                return resp
            else:
                messages.error(request, 'Невірний 2FA токен')
                return render(request, self.template_name, {'show_token_form': True, 'next': next_url})
        else:
            request.session['2fa_user_id'] = user.id
            # зберігаємо backend з authenticate
            if hasattr(user, 'backend'):
                request.session['2fa_backend'] = user.backend
            return render(request, self.template_name, {'show_token_form': True, 'next': next_url})
    
    def verify_token(self, user, token):
        """Перевіряємо 2FA токен та авто-підтверджуємо пристрій при першому успішному коді"""
        # Перевіряємо всі TOTP-пристрої користувача
        for device in TOTPDevice.objects.filter(user=user):
            if device.verify_token(token):
                if not device.confirmed:
                    device.confirmed = True
                    device.save()
                return True
        return False


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_member_required(login_url='admin_2fa_login'), name='dispatch')
class TwoFactorSetupView(View):
    """Налаштування 2FA для користувача"""
    template_name = 'admin/2fa_setup.html'
    
    def get(self, request):
        if not request.user.is_staff:
            messages.error(request, 'Доступ заборонено')
            return redirect('/')
        
        # Створюємо TOTP пристрій якщо його немає
        device, created = TOTPDevice.objects.get_or_create(
            user=request.user,
            name='Microsoft Authenticator'
        )
        
        if created:
            device.save()
        
        # Генеруємо QR код
        qr_data = device.config_url
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        context = {
            'device': device,
            'qr_code': qr_code,
            'backup_tokens': StaticToken.objects.filter(user=request.user)
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        token = request.POST.get('token')
        device = TOTPDevice.objects.filter(user=request.user, name='Microsoft Authenticator').first()
        
        if not device:
            messages.error(request, 'Пристрій не знайдено')
            return redirect('2fa_setup')
        
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            messages.success(request, '2FA успішно налаштовано!')
            return redirect('/admin/')
        else:
            messages.error(request, 'Невірний токен. Спробуйте ще раз.')
            return redirect('2fa_setup')
