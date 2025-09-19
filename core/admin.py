from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Tag
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.conf import settings
from django.core.mail import EmailMessage
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
from io import BytesIO

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'slug', 'name_uk', 'name_en']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('🏷️ Основна інформація', {
            'fields': ('name', 'slug')
        }),
        ('🌍 Багатомовність', {
            'fields': ('name_en', 'name_uk', 'name_pl'),
            'classes': ('collapse',)
        }),
        ('🎨 Дизайн', {
            'fields': ('icon', 'color', 'category')
        }),
        ('⚙️ Налаштування', {
            'fields': ('description', 'is_active', 'is_featured')
        })
    )

def send_2fa_qr(modeladmin, request, queryset):
    sent = 0
    for user in queryset:
        if not user.email:
            continue
        TOTPDevice.objects.filter(user=user).delete()
        device = TOTPDevice.objects.create(user=user, name='Microsoft Authenticator')
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(device.config_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        email = EmailMessage(
            subject='LAZYSOFT Admin 2FA',
            body=f'Скануйте QR у Microsoft Authenticator або використайте URL: {device.config_url}',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'info@lazysoft.pl',
            to=[user.email]
        )
        email.attach(f'2fa_qr_{user.username}.png', buffer.getvalue(), 'image/png')
        email.send()
        sent += 1
    modeladmin.message_user(request, f'Надіслано {sent} QR')

send_2fa_qr.short_description = 'Надіслати 2FA QR на email'

class CustomUserAdmin(UserAdmin):
    actions = [send_2fa_qr]

try:
    admin.site.unregister(User)
except Exception:
    pass
admin.site.register(User, CustomUserAdmin)