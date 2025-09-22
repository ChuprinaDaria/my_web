# pricing/apps.py
from django.apps import AppConfig


class PricingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pricing'
    verbose_name = '💰 Управління цінами'