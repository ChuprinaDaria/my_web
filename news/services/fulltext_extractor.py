import requests
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class FullTextExtractor:
    """Витягує повний текст статей через FiveFilters"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'FIVEFILTERS_BASE_URL', 'http://localhost:8082')
        self.timeout = getattr(settings, 'FIVEFILTERS_TIMEOUT', 30)
        self.enabled = getattr(settings, 'FIVEFILTERS_ENABLED', True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LAZYSOFT-NewsBot/1.0'
        })
        
    def extract_article(self, url: str) -> Optional[str]:
        """Витягує повний текст однієї статті"""
        if not self.enabled:
            logger.debug("FiveFilters вимкнений")
            return None
            
        try:
            logger.debug(f"🔍 Full-text extraction: {url}")
            
            response = self.session.get(
                f"{self.base_url}/extract.php",
                params={'url': url, 'format': 'json'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('content', '')
                
                if content and len(content.strip()) > 100:
                    logger.info(f"✅ Full-text отримано: {len(content)} символів")
                    return content.strip()
                else:
                    logger.debug("⚠️ Full-text порожній або занадто короткий")
            else:
                logger.warning(f"⚠️ FiveFilters HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout для {url}")
        except Exception as e:
            logger.warning(f"❌ Помилка full-text для {url}: {e}")
            
        return None