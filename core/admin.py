from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Tag, HomeHero, AboutCard, CoreOgImage
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
@admin.register(HomeHero)
class HomeHeroAdmin(admin.ModelAdmin):
    list_display = [
        'heading_en', 'is_active', 'heading_uk', 'heading_pl', 'updated_at'
    ]
    list_display_links = ['heading_en']
    list_editable = ['is_active']
    fieldsets = (
        ('Статус', {'fields': ('is_active',)}),
        ('Заголовок', {'fields': ('heading_uk', 'heading_pl', 'heading_en')}),
        ('Підзаголовок', {'fields': ('subheading_uk', 'subheading_pl', 'subheading_en')}),
        ('Опис', {'fields': ('description_uk', 'description_pl', 'description_en')}),
        ('CTA основна', {'fields': ('cta_primary_label_uk','cta_primary_label_pl','cta_primary_label_en','cta_primary_url')}),
        ('CTA додаткова', {'fields': ('cta_secondary_label_uk','cta_secondary_label_pl','cta_secondary_label_en','cta_secondary_url')}),
        ('Службове', {'fields': ('updated_at',)}),
    )
    readonly_fields = ['updated_at']


@admin.register(AboutCard)
class AboutCardAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'is_active', 'order', 'updated_at']
    list_display_links = ['title_en']
    list_editable = ['is_active', 'order']
    readonly_fields = ['updated_at']

    fieldsets = (
        ('📋 Статус', {
            'fields': ('is_active', 'order')
        }),
        ('📝 Заголовки', {
            'fields': ('title_uk', 'title_pl', 'title_en')
        }),
        ('📖 Описи', {
            'fields': ('description_uk', 'description_pl', 'description_en')
        }),
        ('🖼️ Зображення', {
            'fields': ('image',),
            'description': 'Рекомендований розмір: 600x400px'
        }),
        ('🔗 URL', {
            'fields': ('url',),
            'description': 'URL сторінки About (буде додано префікс мови автоматично)'
        }),
        ('📅 Службове', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(CoreOgImage)
class CoreOgImageAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order', 'updated_at']
    list_editable = ['is_active', 'order']

    readonly_fields = ['updated_at']


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