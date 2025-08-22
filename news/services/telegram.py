import json
import logging
import os
from urllib.parse import urlparse

import requests
from django.conf import settings


logger = logging.getLogger(__name__)

def _get_chat_id(language: str | None = None) -> str:
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)
    if chat_id:
        return chat_id
    if language == "uk":
        chat_id = getattr(settings, "TELEGRAM_CHANNEL_UK", None)
    elif language == "en":
        chat_id = getattr(settings, "TELEGRAM_CHANNEL_EN", None)
    elif language == "pl":
        chat_id = getattr(settings, "TELEGRAM_CHANNEL_PL", None)
    return chat_id or getattr(settings, "TELEGRAM_CHANNEL_UK", None)

def _dump_markup(reply_markup):
    if not reply_markup:
        return None
    # Telegram очікує JSON-рядок
    return json.dumps(reply_markup, ensure_ascii=False)

def _tg_request(method: str, data: dict, files=None):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, data=data, files=files, timeout=20)
    except Exception as e:
        logger.exception("TG request failed (network): %s", e)
        raise

    if r.status_code != 200:
        desc = r.text
        try:
            desc = r.json().get("description", desc)
        except Exception:
            pass
        safe_payload = {k: v for k, v in data.items() if k not in {"photo"}}
        logger.error("TG %s -> %s %s | payload=%s", method, r.status_code, desc, safe_payload)
        raise requests.HTTPError(f"Telegram API error {r.status_code}: {desc}")
    return r.json()

def _looks_public_image_url(url: str) -> bool:
    """true якщо це не localhost і схоже на публічну картинку"""
    if not url or not url.startswith(("http://", "https://")):
        return False
    host = urlparse(url).hostname or ""
    if host in {"127.0.0.1", "localhost"}:
        return False
    # легка перевірка по розширенню; без HEAD, щоб не ловити фейли
    return url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))

# ---------- API ----------

def tg_send_message(text: str, language: str = "uk", reply_markup=None, unpin=True) -> str:
    chat_id = _get_chat_id(language)
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    dumped = _dump_markup(reply_markup)
    if dumped:
        data["reply_markup"] = dumped

    res = _tg_request("sendMessage", data)
    mid = res.get("result", {}).get("message_id")

    if unpin and mid:
        try:
            _tg_request("unpinChatMessage", {"chat_id": chat_id, "message_id": mid})
        except Exception as e:
            logger.warning("Не вдалося зняти пін: %s", e)
    return str(mid) if mid else ""

def tg_send_photo(photo_path_or_url: str, caption: str, language: str = "uk", reply_markup=None, unpin=True) -> str:
    """
    Проста логіка:
    - якщо є робоче локальне фото -> sendPhoto(files)
    - elif є публічний image-URL (не localhost) -> sendPhoto(url)
    - інакше -> fallback на tg_send_message(caption)
    """
    chat_id = _get_chat_id(language)

    # 1) Локальний файл
    if photo_path_or_url and os.path.exists(photo_path_or_url):
        try:
            with open(photo_path_or_url, "rb") as f:
                data = {
                    "chat_id": chat_id,
                    "caption": caption[:1024],
                    "parse_mode": "HTML",
                }
                dumped = _dump_markup(reply_markup)
                if dumped:
                    data["reply_markup"] = dumped
                files = {"photo": (os.path.basename(photo_path_or_url), f)}
                res = _tg_request("sendPhoto", data, files=files)
        except Exception as e:
            logger.info("Фото не прочиталось (%s). Відправляю текст.", e)
            return tg_send_message(caption, language, reply_markup, unpin)

    # 2) Публічний URL
    elif _looks_public_image_url(photo_path_or_url):
        try:
            data = {
                "chat_id": chat_id,
                "photo": photo_path_or_url,
                "caption": caption[:1024],
                "parse_mode": "HTML",
            }
            dumped = _dump_markup(reply_markup)
            if dumped:
                data["reply_markup"] = dumped
            res = _tg_request("sendPhoto", data)
        except Exception as e:
            logger.info("Не вдалося відправити фото за URL (%s). Відправляю текст.", e)
            return tg_send_message(caption, language, reply_markup, unpin)

    # 3) Фолбек: фото немає або воно локалхост/html/що завгодно
    else:
        logger.info("Фото відсутнє або недоступне — відправляю тільки текст")
        return tg_send_message(caption, language, reply_markup, unpin)

    mid = res.get("result", {}).get("message_id")
    if unpin and mid:
        try:
            _tg_request("unpinChatMessage", {"chat_id": chat_id, "message_id": mid})
        except Exception as e:
            logger.warning("Не вдалося зняти пін (photo): %s", e)
    return str(mid) if mid else ""