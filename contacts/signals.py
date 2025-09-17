from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ContactSubmission
from .views import sync_submission_to_asana

@receiver(post_save, sender=ContactSubmission)
def sync_status_change_to_asana(sender, instance, created, **kwargs):
    """Автоматично синхронізуємо зміни статусу з Asana"""
    if not created and instance.asana_task_id:  # Тільки для оновлень
        sync_submission_to_asana(instance)
