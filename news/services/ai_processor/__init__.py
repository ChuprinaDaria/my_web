# news/services/ai_processor/__init__.py

"""
LAZYSOFT AI News Processor - Модульна система обробки новин

Структура:
- ai_processor_base.py     - Базовий клас з AI клієнтами
- ai_processor_content.py  - Створення тримовного контенту  
- ai_processor_helpers.py  - SEO, CTA, зображення
- ai_processor_main.py     - Основна обробка статей
- ai_processor_database.py - Збереження в базу даних

Використання:
    from news.services.ai_processor import AINewsProcessor
    
    processor = AINewsProcessor()
    result = processor.process_article(raw_article)
"""

from .ai_processor_main import AINewsProcessor
from .ai_processor_base import ProcessedContent

# Експортуємо основні класи
__all__ = [
    'AINewsProcessor',
    'ProcessedContent',
]

# Версія AI процесора
__version__ = '2.0.0'

# Логування
import logging
logger = logging.getLogger(__name__)
logger.info("🤖 LAZYSOFT AI News Processor v%s завантажено", __version__)