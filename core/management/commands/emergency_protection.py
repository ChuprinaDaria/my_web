from django.core.management.base import BaseCommand
from core.services.cloudflare_api import CloudflareAPI

class Command(BaseCommand):
    help = 'Emergency захист через Cloudflare'
    
    def add_arguments(self, parser):
        parser.add_argument('--action', type=str, choices=['under_attack', 'normal', 'block_ip', 'challenge_ip'], 
                          help='Дія для виконання')
        parser.add_argument('--ip', type=str, help='IP адреса для блокування/challenge')
        parser.add_argument('--reason', type=str, default='Emergency protection', help='Причина блокування')
    
    def handle(self, *args, **options):
        action = options['action']
        cf = CloudflareAPI()
        
        if action == 'under_attack':
            if cf.enable_under_attack_mode():
                self.stdout.write(self.style.SUCCESS('🚨 UNDER ATTACK MODE ENABLED'))
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to enable Under Attack Mode'))
                
        elif action == 'normal':
            if cf.disable_under_attack_mode():
                self.stdout.write(self.style.SUCCESS('✅ Security level set to Normal'))
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to disable Under Attack Mode'))
                
        elif action == 'block_ip':
            ip = options['ip']
            reason = options['reason']
            if ip and cf.block_ip(ip, reason):
                self.stdout.write(self.style.SUCCESS(f'🚫 IP {ip} blocked: {reason}'))
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to block IP'))
                
        elif action == 'challenge_ip':
            ip = options['ip']
            reason = options['reason']
            if ip and cf.challenge_ip(ip, reason):
                self.stdout.write(self.style.SUCCESS(f'🤖 IP {ip} challenged: {reason}'))
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to challenge IP'))
        else:
            self.stdout.write(self.style.ERROR('❌ Invalid action specified'))
