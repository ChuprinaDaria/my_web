from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Показує статистику Linus Security System'
    
    def handle(self, *args, **options):
        today_blocks = cache.get('linus_blocks_today', 0)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"""
🖕 LINUS SECURITY REPORT 🖕

Today's victims: {today_blocks}
- Scanners rekt: {cache.get('scanners_today', 0)}
- Brute force stopped: {cache.get('bruteforce_today', 0)}
- SQL kids blocked: {cache.get('sqli_today', 0)}

Status: OPERATIONAL & SARCASTIC 🤘
                """
            )
        )
