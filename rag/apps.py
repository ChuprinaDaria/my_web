# rag/apps.py
from django.apps import AppConfig


class RagConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag'
    verbose_name = '🧠 RAG Консультант'
    
    def ready(self):
        # Імпортуємо сигнали для автоматичної індексації
        import rag.signals