from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
import requests
import json

class Command(BaseCommand):
    help = 'Тестує безпекові заголовки сайту'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='http://127.0.0.1:8000',
            help='URL сайту для тестування'
        )

    def handle(self, *args, **options):
        url = options['url']
        
        self.stdout.write(
            self.style.SUCCESS(f'🔒 Тестуємо безпекові заголовки для {url}')
        )
        
        try:
            response = requests.get(url, timeout=10)
            headers = response.headers
            
            # Перевіряємо наявність основних заголовків безпеки
            security_headers = {
                'Content-Security-Policy': 'CSP',
                'Strict-Transport-Security': 'HSTS',
                'X-Content-Type-Options': 'X-Content-Type-Options',
                'X-Frame-Options': 'X-Frame-Options',
                'X-XSS-Protection': 'X-XSS-Protection',
                'Referrer-Policy': 'Referrer-Policy',
                'Permissions-Policy': 'Permissions-Policy',
                'Cross-Origin-Embedder-Policy': 'COEP',
                'Cross-Origin-Opener-Policy': 'COOP',
                'Cross-Origin-Resource-Policy': 'CORP'
            }
            
            self.stdout.write('\n📋 Результати перевірки заголовків:')
            self.stdout.write('=' * 50)
            
            for header, name in security_headers.items():
                if header in headers:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {name}: {headers[header]}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {name}: ВІДСУТНІЙ')
                    )
            
            # Спеціальна перевірка CSP
            if 'Content-Security-Policy' in headers:
                csp = headers['Content-Security-Policy']
                if 'require-trusted-types-for' in csp:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Trusted Types: Налаштовано')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  Trusted Types: Відсутній')
                    )
            
            # Перевірка HSTS
            if 'Strict-Transport-Security' in headers:
                hsts = headers['Strict-Transport-Security']
                if 'includeSubDomains' in hsts:
                    if 'preload' in hsts:
                        self.stdout.write(
                            self.style.SUCCESS('✅ HSTS: Повністю налаштовано (production)')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS('✅ HSTS: Налаштовано (development mode)')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  HSTS: Неповна конфігурація')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ HSTS: ВІДСУТНІЙ')
                )
            
            self.stdout.write('\n🎯 Рекомендації:')
            self.stdout.write('=' * 50)
            
            missing_headers = [name for header, name in security_headers.items() 
                             if header not in headers]
            
            if missing_headers:
                self.stdout.write(
                    self.style.WARNING(f'Додайте відсутні заголовки: {", ".join(missing_headers)}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('🎉 Всі основні заголовки безпеки налаштовані!')
                )
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Помилка при підключенні до {url}: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Неочікувана помилка: {e}')
            )
