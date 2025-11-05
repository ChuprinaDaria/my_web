import re
from django import template

register = template.Library()


@register.filter
def youtube_embed(url):
    """
    Конвертує YouTube URL в embed формат

    Підтримує формати:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID (вже embed)
    """
    if not url:
        return url

    # Якщо вже embed формат - повертаємо як є
    if 'youtube.com/embed/' in url:
        return url

    # Регулярні вирази для різних форматів YouTube
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f'https://www.youtube.com/embed/{video_id}'

    # Якщо це Vimeo
    vimeo_match = re.search(r'vimeo\.com/(\d+)', url)
    if vimeo_match:
        video_id = vimeo_match.group(1)
        return f'https://player.vimeo.com/video/{video_id}'

    # Якщо не розпізнали формат, повертаємо оригінальний URL
    return url
