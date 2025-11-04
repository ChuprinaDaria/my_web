from django.utils.deprecation import MiddlewareMixin
import logging
import re

logger = logging.getLogger('sitemap')

class SitemapRobotsMiddleware(MiddlewareMixin):
    """
    Middleware для виключення sitemap з noindex headers
    """

    def process_response(self, request, response):
        # Перевіряємо чи це sitemap
        if 'sitemap' in request.path:
            # Видаляємо X-Robots-Tag якщо він є
            if 'X-Robots-Tag' in response:
                logger.info(f"Removing X-Robots-Tag from sitemap: {request.path}")
                del response['X-Robots-Tag']

            # Встановлюємо правильний robots header для sitemap
            response['X-Robots-Tag'] = 'index, follow'
            logger.info(f"Set X-Robots-Tag to 'index, follow' for sitemap: {request.path}")

            # Очищуємо sitemap від script тегів (додаються браузерними розширеннями)
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')

                # Видаляємо всі script теги
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                content = re.sub(r'<script[^>]*/?>', '', content)

                response.content = content.encode('utf-8')
                logger.info(f"Cleaned script tags from sitemap: {request.path}")

        return response
