from django.core.management.base import BaseCommand
from core.services.cloudflare_api import get_cloudflare_stats

class Command(BaseCommand):
    help = 'Показує статистику Cloudflare захисту'
    
    def handle(self, *args, **options):
        stats = get_cloudflare_stats()
        
        rate_limits = stats.get('rate_limits', [])
        rate_limits_count = len(rate_limits) if rate_limits else 0
        
        self.stdout.write(
            self.style.SUCCESS(
                f"""
☁️ CLOUDFLARE SECURITY REPORT ☁️

Under Attack Mode: {'🚨 ENABLED' if stats.get('under_attack_mode') else '✅ Normal'}
Zone Analytics: {'📊 Available' if stats.get('zone_analytics') else '❌ Not available'}
Security Events: {'🔍 Available' if stats.get('security_events') else '❌ Not available'}
Rate Limits: {rate_limits_count} rules active

Status: {'🚨 EMERGENCY MODE' if stats.get('under_attack_mode') else '🛡️ PROTECTED'}
                """
            )
        )
