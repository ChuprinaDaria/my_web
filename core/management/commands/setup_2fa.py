# core/management/commands/setup_2fa.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticToken, StaticDevice
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64


class Command(BaseCommand):
    help = 'Налаштування 2FA для адміністратора'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Ім\'я користувача адміністратора')
        parser.add_argument('--create-admin', action='store_true', help='Створити адміністратора якщо не існує')

    def handle(self, *args, **options):
        username = options.get('username') or 'admin'
        
        # Створюємо або отримуємо користувача
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Знайдено користувача: {username}')
        except User.DoesNotExist:
            if options.get('create_admin'):
                user = User.objects.create_superuser(
                    username=username,
                    email='admin@lazysoft.com.ua',
                    password='admin123'  # Змініть пароль!
                )
                self.stdout.write(f'Створено адміністратора: {username}')
            else:
                self.stdout.write(self.style.ERROR(f'Користувач {username} не знайдений. Використайте --create-admin для створення.'))
                return

        # Створюємо TOTP пристрій
        device, created = TOTPDevice.objects.get_or_create(
            user=user,
            name='Microsoft Authenticator'
        )
        
        if created:
            device.save()
            self.stdout.write('Створено TOTP пристрій')
        else:
            self.stdout.write('TOTP пристрій вже існує')

        # Генеруємо QR код
        qr_data = device.config_url
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        # Зберігаємо QR код у файл
        with open('2fa_qr_code.png', 'wb') as f:
            f.write(base64.b64decode(qr_code))
        
        self.stdout.write(self.style.SUCCESS('2FA налаштовано успішно!'))
        self.stdout.write(f'QR код збережено у файл: 2fa_qr_code.png')
        self.stdout.write(f'URL для налаштування: {qr_data}')
        
        # Створюємо StaticDevice для резервних токенів
        static_device, created = StaticDevice.objects.get_or_create(
            user=user,
            name='Backup Tokens'
        )
        
        # Створюємо резервні токени
        backup_tokens = []
        for i in range(10):
            token = StaticToken.objects.create(
                device=static_device
            )
            backup_tokens.append(token.token)
        
        self.stdout.write('Резервні токени:')
        for i, token in enumerate(backup_tokens, 1):
            self.stdout.write(f'  {i}. {token}')
        
        self.stdout.write('\nІнструкції:')
        self.stdout.write('1. Встановіть Microsoft Authenticator на телефон')
        self.stdout.write('2. Відскануйте QR код з файлу 2fa_qr_code.png')
        self.stdout.write('3. Перейдіть на http://127.0.0.1:8000/admin/2fa/setup/')
        self.stdout.write('4. Введіть 6-значний код з додатку для підтвердження')
