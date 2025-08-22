import base64
import uuid
import os
from typing import Dict, List
from django.conf import settings
from .ai_processor_base import AINewsProcessor


class AIProcessorHelpers(AINewsProcessor):
    """Допоміжні функції для AI процесора"""

    def _generate_seo_metadata(self, content_data: Dict, category: str) -> Dict:
        """Генерує SEO метадані для всіх мов"""
        
        seo_data = {}
        
        # Для кожної мови генеруємо SEO
        for lang in ['en', 'uk', 'pl']:
            title = content_data.get(f'title_{lang}', '')
            summary = content_data.get(f'summary_{lang}', '')
            
            # SEO заголовки (до 60 символів)
            if len(title) <= 60:
                seo_title = title
            else:
                # Скорочуємо зберігаючи сенс
                seo_title = title[:57] + '...'
            
            # SEO описи (до 160 символів)
            if len(summary) <= 160:
                seo_description = summary
            else:
                # Беремо перше речення або скорочуємо
                sentences = summary.split('.')
                if sentences and len(sentences[0]) <= 160:
                    seo_description = sentences[0] + '.'
                else:
                    seo_description = summary[:157] + '...'
            
            seo_data[f'meta_title_{lang}'] = seo_title
            seo_data[f'meta_description_{lang}'] = seo_description
        
        return seo_data

    def _generate_cta_buttons(self, category: str) -> List[Dict]:
        """Генерує CTA кнопки для категорії"""
        
        cta_mapping = {
            'ai': [
                {
                    'text_en': 'Get AI Audit',
                    'text_uk': 'Отримати AI аудит',
                    'text_pl': 'Otrzymać audyt AI',
                    'url': '/services/ai-audit/'
                },
                {
                    'text_en': 'Calculate AI ROI',
                    'text_uk': 'Розрахувати ROI від AI',
                    'text_pl': 'Obliczyć ROI z AI',
                    'url': '/services/ai-roi-calculator/'
                }
            ],
            'automation': [
                {
                    'text_en': 'Start Automation',
                    'text_uk': 'Почати автоматизацію',
                    'text_pl': 'Rozpocząć automatyzację',
                    'url': '/services/business-automation/'
                },
                {
                    'text_en': 'Free Consultation',
                    'text_uk': 'Безкоштовна консультація',
                    'text_pl': 'Darmowa konsultacja',
                    'url': '/contact/'
                }
            ],
            'seo': [
                {
                    'text_en': 'SEO Analysis',
                    'text_uk': 'SEO аналіз',
                    'text_pl': 'Analiza SEO',
                    'url': '/services/seo-audit/'
                }
            ],
            'chatbots': [
                {
                    'text_en': 'Build Chatbot',
                    'text_uk': 'Створити чат-бот',
                    'text_pl': 'Stworzyć chatbota',
                    'url': '/services/chatbot-development/'
                }
            ]
        }
        
        return cta_mapping.get(category, [
            {
                'text_en': 'Learn More',
                'text_uk': 'Дізнатися більше',
                'text_pl': 'Dowiedz się więcej',
                'url': '/services/'
            }
        ])

    def _generate_ai_image(self, prompt: str, size: str = "1024x1024") -> str:
        """
        Генерує зображення через OpenAI Images і повертає public URL.
        Повертає порожній рядок, якщо щось пішло не так.
        """
        if not prompt:
            return ""
        if not getattr(self, "openai_client", None):
            self.logger.warning("[IMAGE] OpenAI клієнт відсутній — пропускаю генерацію")
            return ""

        try:
            # DALL·E 3 або 2 (краще 3 для якості)
            resp = self.openai_client.images.generate(
                model="gpt-image-1",  # або "dall-e-3"
                prompt=prompt,
                size=size,
                n=1
            )

            # новий SDK завжди повертає resp.data[0].url якщо success
            url = getattr(resp.data[0], "url", "") if resp and resp.data else ""
            if url:
                return url

            # fallback на base64 (рідко, але може бути)
            b64 = getattr(resp.data[0], "b64_json", None)
            if b64:
                name = f"ai_{uuid.uuid4().hex}.png"
                out_dir = os.path.join(settings.MEDIA_ROOT, "ai_images")
                os.makedirs(out_dir, exist_ok=True)
                path = os.path.join(out_dir, name)
                with open(path, "wb") as f:
                    f.write(base64.b64decode(b64))

                from django.contrib.sites.models import Site
                domain = getattr(settings, "SITE_URL", None) or f"https://{Site.objects.get_current().domain}"
                return f"{domain}{settings.MEDIA_URL}ai_images/{name}"

            return ""
        except Exception as e:
            self.logger.error(f"[IMAGE] Помилка генерації: {e}")
            return ""


    def _generate_image_prompts(self, content_data: Dict, category: str) -> Dict:
        """
        Генерує ТЕКСТЛЕС (no-text) промпти для AI-зображень у брендовому неон-стилі LAZYSOFT.
        Жодних слів, літер, цифр, логотипів чи підписів — лише чиста візуалка.
        """

        # Категорійні кольори та візуальні мотиви (центральний об'єкт/сюжет)
        category_elements = {
            "ai": {
                "colors": "electric blue, neon pink, bright green accents",
                "elements": "glowing microchip core with neural traces, circuitry, energy beams, subtle particles",
                "mood": "futuristic, intelligent, high-tech"
            },
            "automation": {
                "colors": "cyan, purple, lime accents",
                "elements": "interlocked glossy gears with light trails, robotic arm silhouette, flowing pipes",
                "mood": "precision, motion, efficiency"
            },
            "crm": {
                "colors": "orange, azure, fuchsia accents",
                "elements": "network of glossy nodes connected by luminous lines, abstract user silhouettes",
                "mood": "connections, relationships, clarity"
            },
            "seo": {
                "colors": "vivid green, teal, white highlights",
                "elements": "UPWARD glowing line chart with smooth curve, grid backdrop, light bloom",
                "mood": "growth, analytics, momentum"
            },
            "social": {
                "colors": "hot pink, electric blue, lime accents",
                "elements": "radiating network graph, floating bubbles, interaction pulses",
                "mood": "engagement, energy, vibrancy"
            },
            "chatbots": {
                "colors": "cyan, violet, mint accents",
                "elements": "abstract chat bubble cluster made of glass, soundwave ripples, tiny nodes",
                "mood": "conversation, assistance, clarity"
            },
            "ecommerce": {
                "colors": "orange, blue, yellow accents",
                "elements": "sleek 3D shopping cart silhouette with neon highlights, floating cards and coins",
                "mood": "commerce, speed, trust"
            },
            "fintech": {
                "colors": "gold, emerald, sapphire accents",
                "elements": "shimmering coin and card forms, elegant bars/lines, subtle crypto glyph geometry (no logos)",
                "mood": "finance, innovation, premium"
            },
            "corporate": {
                "colors": "silver, royal blue, violet accents",
                "elements": "minimal skyline of glass towers with rim light, subtle growth bars",
                "mood": "enterprise, stability, scale"
            },
            "general": {
                "colors": "vibrant neon spectrum",
                "elements": "abstract tech shapes, glowing nodes, soft energy streaks",
                "mood": "innovation, modern, clean"
            },
        }

        cat = category_elements.get(category, category_elements["general"])

        # Базовий безтекстовий стиль (1:1, темний фон, неон, скло)
        base_style = f"""
    Create a SQUARE (1:1) high-resolution digital illustration for a tech news cover.
    Dark background with soft vignette. Glassmorphism panels, subtle depth-of-field,
    neon glow accents ({cat['colors']}), clean negative space.

    CENTRAL MOTIF: {cat['elements']}
    MOOD: {cat['mood']}

    COMPOSITION:
    - Single clear focal object centered or slightly off-center.
    - Minimalistic, premium, glossy surfaces with rim lighting and reflections.
    - Optional light streaks and particles for motion/energy.

    STRICTLY NO TEXT:
    - No words, no letters, no numbers, no captions, no logos, no watermarks,
    no stickers, no UI, no titles or tags. Pure imagery only.

    STYLE:
    - Modern cyber/neon aesthetic, elegant, social-media ready.
    - Physically plausible lighting, high contrast, crisp details.
    - Avoid clutter, avoid busy backgrounds.

    OUTPUT: a single image only.
    """

        # Оскільки зображення БЕЗ тексту — усі 3 промпти ідентичні
        return {
            "ai_image_prompt_en": base_style.strip(),
            "ai_image_prompt_uk": base_style.strip(),
            "ai_image_prompt_pl": base_style.strip(),
        }