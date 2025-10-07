# consultant/views.py - оновлена версія з RAG
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
import json
import uuid
import time

from .models import ChatSession, Message, ConsultantProfile, KnowledgeBase, ChatAnalytics
from services.asana_service import asana_service
from news.services.telegram import _tg_request
from .rag_integration import enhanced_consultant

# Імпортуємо pricing моделі якщо доступні
try:
    from pricing.models import QuoteRequest
    PRICING_AVAILABLE = True
except ImportError:
    PRICING_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)


def _get_company_brand_context():
    try:
        from contacts.models import CompanyInfo
        brand = CompanyInfo.objects.filter(is_active=True).first()
        if brand:
            return brand
    except Exception as e:
        logger.warning(f"CompanyInfo not available: {e}")
    class Fallback:
        company_name = "LAZYSOFT"
        website = "lazysoft.dev"
        logo = None
        address_line1 = "Edwarda Dembowskiego 98/1"
        city = "Wrocław"
        postal_code = "51-669"
        country = "Poland"
        email = "info@lazysoft.pl"
        phone = "+48 727 842 737"
        tax_id = ""
        authorized_person = "Daria Chuprina"
    return Fallback()
# Трек кліку на консультацію: створюємо таск в Asana і надсилаємо в Telegram
@csrf_exempt
@require_http_methods(["POST"])
def track_consultation_click(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        name = data.get('name', '')
        email = data.get('email', '')
        url = data.get('url', '')

        notes = (
            f"Клік на консультацію з чату\n\n"
            f"Session: {session_id}\n"
            f"Ім'я: {name}\nEmail: {email}\nURL: {url}"
        )
        try:
            if asana_service:
                asana_service.create_generic_task("Клік на консультацію (чат)", notes, due_days=2)
        except Exception as e:
            logger.error(f"Asana error (consultation click): {e}")

        try:
            admin_chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)
            if admin_chat_id:
                data = {
                    "chat_id": admin_chat_id,
                    "text": f"📅 Клік на консультацію з чату\n{notes}",
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                }
                _tg_request("sendMessage", data)
        except Exception as e:
            logger.error(f"Telegram error (consultation click): {e}")

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



def _ensure_items(items):
    safe_items = []
    if isinstance(items, list):
        for it in items:
            if not isinstance(it, dict):
                continue
            safe_items.append({
                'title': it.get('title', 'Послуга'),
                'pkg': it.get('pkg', ''),
                'price': it.get('price', '-'),
                'currency': it.get('currency', ''),
                'assumptions': it.get('assumptions', '')
            })
    if not safe_items:
        safe_items = [{
            'title': 'Послуга',
            'pkg': '',
            'price': '-',
            'currency': '',
            'assumptions': ''
        }]
    return safe_items


def _render_proposal_pdf(context):
    try:
        html = render_to_string('quotes/proposal.html', context)
    except Exception:
        # Fallback мінімальний HTML, якщо шаблон відсутній
        html = f"""
        <html><body>
          <h1>Комерційна пропозиція</h1>
          <p>Клієнт: {context.get('name')}</p>
          <p>Email: {context.get('email')}</p>
          <ul>
            {''.join([f"<li>{it.get('title')} — {it.get('pkg')} — {it.get('price')} {it.get('currency')}</li>" for it in context.get('items', [])])}
          </ul>
          <p>{context.get('notes','')}</p>
        </body></html>
        """
    pdf_bytes = None
    try:
        import importlib
        weasyprint_module = importlib.import_module('weasyprint')
        html_renderer = getattr(weasyprint_module, 'HTML', None)
        if html_renderer:
            pdf_bytes = html_renderer(string=html, base_url=getattr(settings, 'SITE_URL', None)).write_pdf()
        else:
            raise ImportError('weasyprint.HTML not found')
    except Exception as e:
        logger.warning(f"WeasyPrint not available or failed, sending HTML instead: {e}")
    return html, pdf_bytes


def _send_proposal_email(to_email, subject, html_body, pdf_bytes=None):
    """Надсилає пропозицію клієнту; повертає True/False, логує помилки, дублює адміну."""
    try:
        admin_email = getattr(settings, 'SALES_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@localhost')

        email = EmailMessage(
            subject=subject,
            body=html_body,
            from_email=from_email,
            to=[to_email],
            bcc=[admin_email] if admin_email else None,
        )
        try:
            email.charset = 'utf-8'
        except Exception:
            pass
        # reply-to як брендова адреса, якщо доступна
        try:
            brand = _get_company_brand_context()
            reply_to = [getattr(brand, 'email', None)] if getattr(brand, 'email', None) else []
            if reply_to:
                email.reply_to = reply_to
        except Exception:
            pass

        email.content_subtype = 'html'
        if pdf_bytes:
            email.attach('proposal.pdf', pdf_bytes, 'application/pdf')
        else:
            email.attach('proposal.html', html_body.encode('utf-8'), 'text/html')
        email.send(fail_silently=False)
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def consultant_chat(request):
    """Головна сторінка чату з консультантом"""
    consultant = ConsultantProfile.objects.filter(is_active=True).first()
    if not consultant:
        consultant = ConsultantProfile.objects.create()
    
    context = {
        'consultant': consultant,
        'page_title': 'RAG Консультант',
        'page_description': 'Спілкуйтесь з нашим штучним інтелектом консультантом',
    }
    return render(request, 'consultant/chat.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def start_chat_session(request):
    """Почати нову сесію чату"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', str(uuid.uuid4()))
        language = data.get('language')
        
        # Створюємо або отримуємо сесію
        chat_session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': request.user if request.user.is_authenticated else None,
                'user_ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
        # Зберігаємо вибір мови як системне повідомлення на початку сесії
        if language:
            Message.objects.filter(
                chat_session=chat_session,
                role='system',
                content__startswith='language:'
            ).delete()
            Message.objects.create(chat_session=chat_session, role='system', content=f"language:{language}")
        
        # Створюємо аналітику для нової сесії
        if created:
            ChatAnalytics.objects.create(chat_session=chat_session)
        
        return JsonResponse({
            'success': True,
            'session_id': str(chat_session.id),
            'created': created
        })
    
    except Exception as e:
        logger.error(f"Помилка start_chat_session: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Відправити повідомлення консультанту - ОНОВЛЕНО З RAG"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        language = data.get('language')
        message_content = data.get('message', '').strip()
        
        if not session_id or not message_content:
            return JsonResponse({
                'success': False,
                'error': 'Session ID та повідомлення обов\'язкові'
            }, status=400)
        
        # Отримуємо сесію чату
        chat_session = get_object_or_404(ChatSession, id=session_id)
        
        # Зберігаємо повідомлення користувача
        user_message = Message.objects.create(
            chat_session=chat_session,
            role='user',
            content=message_content
        )
        
        # 🚀 НОВА RAG ЛОГІКА - замість простого алгоритму
        if language:
            Message.objects.filter(
                chat_session=chat_session,
                role='system',
                content__startswith='language:'
            ).delete()
            Message.objects.create(chat_session=chat_session, role='system', content=f"language:{language}")
        rag_result = enhanced_consultant.generate_response(message_content, chat_session)
        
        # Зберігаємо відповідь консультанта з RAG метаданими
        assistant_message = Message.objects.create(
            chat_session=chat_session,
            role='assistant',
            content=rag_result['content'],
            is_processed=True,
            processing_time=rag_result['processing_time'],
            tokens_used=rag_result['tokens_used']
        )
        
        # Оновлюємо аналітику
        analytics, _ = ChatAnalytics.objects.get_or_create(chat_session=chat_session)
        analytics.user_messages += 1
        analytics.assistant_messages += 1
        analytics.total_messages += 2
        analytics.total_tokens_used += rag_result['tokens_used']
        analytics.save()
        
        # 💰 Логіка для pricing запитів - ВИДАЛЕНО АВТОМАТИЧНЕ ВІДКРИТТЯ
        additional_data = {}
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': str(assistant_message.id),
                'role': assistant_message.role,
                'content': assistant_message.content,
                'created_at': assistant_message.created_at.isoformat(),
                'processing_time': rag_result['processing_time']
            },
            # 🚀 Додаткові RAG дані
            'rag_data': {
                'intent': rag_result['intent'],
                'sources': rag_result['sources'][:3],  # Топ 3 джерела
                'suggestions': rag_result['suggestions'],
                'actions': rag_result['actions'],
                'method': rag_result['method'],
                'prices_ready': rag_result.get('prices_ready', False),
                'prices': rag_result.get('prices', [])
            },
            **additional_data
        })
    
    except Exception as e:
        logger.error(f"Помилка send_message: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def _extract_services_from_sources(sources):
    """Витягує сервіси з RAG джерел"""
    services = []
    for source in sources:
        if source.get('content_category') == 'service':
            obj = source.get('object')
            if obj:
                services.append({
                    'slug': getattr(obj, 'slug', None),
                    'title': source.get('content_title', str(obj)),
                    'similarity': source.get('similarity', 0)
                })
    return services


# 💰 НОВІ API для pricing інтеграції
@csrf_exempt
@require_http_methods(["POST"])
def request_quote_from_chat(request):
    """Запит прорахунку з чату"""
    if not PRICING_AVAILABLE:
        return JsonResponse({'error': 'Pricing система недоступна'}, status=400)
    
    try:
        data = json.loads(request.body)
        language = (data.get('language') or '').lower()
        
        # Валідація
        required_fields = ['client_name', 'client_email', 'message']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'Поле {field} обов\'язкове'}, status=400)
        
        session_id = data.get('session_id')
        chat_session = None
        
        # Шукаємо сесію для контексту
        if session_id:
            try:
                chat_session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                pass
        # Якщо мова не передана — беремо з системного повідомлення сесії
        if (not language) and chat_session:
            try:
                sys_msg = chat_session.messages.filter(role='system', content__startswith='language:').order_by('-created_at').first()
                if sys_msg and ':' in sys_msg.content:
                    language = sys_msg.content.split(':', 1)[1].strip().lower()
            except Exception:
                pass
        if language not in ('uk', 'pl', 'en'):
            language = 'uk'
        
        # Визначаємо сервіс з контексту чату
        detected_service = None
        if chat_session:
            recent_messages = chat_session.messages.filter(role='user').order_by('-created_at')[:3]
            recent_text = ' '.join([msg.content for msg in recent_messages])
            detected_service = _detect_service_from_text(recent_text)
        
        # Створюємо запит на прорахунок
        quote_request = QuoteRequest.objects.create(
            client_name=data['client_name'],
            client_email=data['client_email'],
            client_phone=data.get('client_phone', ''),
            client_company=data.get('client_company', ''),
            original_query=data['message'],
            service_category=detected_service,
            session_id=str(session_id) if session_id else None,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='new'
        )
        
        # Побудова контексту для PDF
        brand = _get_company_brand_context()

        # Формуємо items з реального ціноутворення
        items = []
        try:
            from pricing.models import ServicePricing
            pricing_qs = ServicePricing.objects.filter(is_active=True)
            if detected_service:
                pricing_qs = pricing_qs.filter(service_category=detected_service)
            pricing_qs = pricing_qs.select_related('service_category', 'tier').order_by('tier__order', 'order')
            for sp in list(pricing_qs[:3]):
                # Локалізація назв
                lang = (language or 'uk').lower()
                service_title = getattr(sp.service_category, f'title_{lang}', getattr(sp.service_category, 'title_en', str(sp.service_category)))
                tier_name = getattr(sp.tier, f'display_name_{lang}', getattr(sp.tier, 'display_name_en', str(sp.tier)))
                if getattr(sp, 'price_to', None) and sp.price_to and sp.price_to != sp.price_from:
                    price_str = f"{int(sp.price_from)}-{int(sp.price_to)}"
                else:
                    price_str = f"{int(sp.price_from)}"
                features = []
                try:
                    features = sp.get_features_list(lang=lang)[:5]
                except Exception:
                    pass
                assumptions = "; ".join(features) if features else ''
                items.append({
                    'title': service_title,
                    'pkg': tier_name,
                    'price': price_str,
                    'currency': 'USD',
                    'assumptions': assumptions
                })
        except Exception as e:
            logger.warning(f"Не вдалося побудувати items з ServicePricing: {e}")

        if not items:
            items = _ensure_items(data.get('items', []))

        # Абсолютний URL для логотипа у листі
        brand_logo_url = None
        try:
            site_url = getattr(settings, 'SITE_URL', '')
            if site_url and getattr(brand, 'logo', None):
                logo_url = getattr(getattr(brand, 'logo', None), 'url', None)
                if logo_url:
                    brand_logo_url = site_url.rstrip('/') + logo_url
        except Exception:
            pass
        # URL на календар (RAG_SETTINGS або CONSULTATION_CALENDAR_URL)
        calendly_url = getattr(settings, 'RAG_SETTINGS', {}).get('CONSULTATION_CALENDAR_URL') or getattr(settings, 'CONSULTATION_CALENDAR_URL', '')

        ctx = {
            'brand': brand,
            'brand_logo_url': brand_logo_url,
            'issued_at': timezone.now(),
            'name': data['client_name'],
            'email': data['client_email'],
            'company': data.get('client_company', ''),
            'notes': data.get('message', ''),
            'items': items,
            'language': (language or 'uk').lower(),
            'calendly_url': calendly_url
        }
        html, pdf_bytes = _render_proposal_pdf(ctx)
        
        # Локалізована тема листа
        subj_map = {
            'uk': 'Комерційна пропозиція',
            'pl': 'Oferta handlowa',
            'en': 'Commercial Proposal',
        }
        # Відправляємо на email клієнта
        sent_ok = _send_proposal_email(
            to_email=data['client_email'],
            subject=subj_map.get(language, 'Commercial Proposal'),
            html_body=html,
            pdf_bytes=pdf_bytes
        )
        # Оновлюємо статус запиту
        try:
            quote_request.email_sent = bool(sent_ok)
            quote_request.pdf_generated = bool(pdf_bytes)
            quote_request.status = 'quoted'
            quote_request.save(update_fields=['email_sent', 'pdf_generated', 'status'])
        except Exception:
            pass

        # Фоново: створити таск в Asana і сповістити в Telegram
        try:
            import threading
            def background():
                try:
                    if asana_service:
                        task_id = asana_service.create_quote_task(quote_request)
                        if task_id:
                            try:
                                quote_request.asana_task_id = task_id
                                quote_request.save(update_fields=['asana_task_id'])
                            except Exception:
                                pass
                except Exception as e:
                    logger.error(f"Asana error for quote: {e}")
                try:
                    asana_task_id_local = None
                    try:
                        asana_task_id_local = task_id if 'task_id' in locals() and task_id else getattr(quote_request, 'asana_task_id', None)
                    except Exception:
                        asana_task_id_local = getattr(quote_request, 'asana_task_id', None)
                    asana_link = f"https://app.asana.com/0/0/{asana_task_id_local}" if asana_task_id_local else "Не створено"
                    msg = (
                        f"📨 НОВИЙ ЗАПИТ НА ПРОРАХУНОК\n\n"
                        f"👤 {quote_request.client_name} | {quote_request.client_email}\n"
                        f"🏢 {quote_request.client_company or '—'} | 📞 {quote_request.client_phone or '—'}\n\n"
                        f"📝 {quote_request.original_query[:500]}{'...' if len(quote_request.original_query) > 500 else ''}\n\n"
                        f"🔗 Asana таск: <a href=\"{asana_link}\">Перейти до таска</a>"
                    )
                    admin_chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)
                    if admin_chat_id:
                        data = {
                            "chat_id": admin_chat_id,
                            "text": msg,
                            "parse_mode": "HTML",
                            "disable_web_page_preview": False,
                        }
                        _tg_request("sendMessage", data)
                except Exception as e:
                    logger.error(f"Telegram error for quote: {e}")
            t = threading.Thread(target=background)
            t.daemon = True
            t.start()
        except Exception:
            pass
        
        # TODO: Відправити в Celery для асинхронної обробки PDF та email
        # generate_quote_pdf.delay(quote_request.id)
        
        return JsonResponse({
            'success': True,
            'message': 'Запит отримано. Надіслали комерційну пропозицію на ваш email.' if sent_ok else 'Запит отримано. Сталася проблема з відправкою email — ми надішлемо пропозицію вручну найближчим часом.',
            'quote_id': quote_request.id,
            'email_sent': bool(sent_ok)
        })
        
    except Exception as e:
        logger.error(f"Помилка request_quote_from_chat: {e}")
        return JsonResponse({'error': 'Помилка обробки запиту'}, status=500)


def _detect_service_from_text(text):
    """Спрощене визначення сервісу з тексту"""
    try:
        from services.models import ServiceCategory
        
        text_lower = text.lower()
        
        # Ключові слова для різних сервісів
        service_keywords = {
            'web-development': ['сайт', 'вебсайт', 'інтернет-магазин', 'landing', 'веб'],
            'mobile-app': ['додаток', 'мобільний', 'app', 'ios', 'android'],
            'ai-automation': ['автоматизація', 'ai', 'штучний інтелект', 'бот'],
            'design': ['дизайн', 'графіка', 'логотип', 'брендинг'],
        }
        
        for service_slug, keywords in service_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                try:
                    return ServiceCategory.objects.get(slug=service_slug)
                except ServiceCategory.DoesNotExist:
                    continue
                    
    except ImportError:
        pass
    
    return None


def _get_client_ip(request):
    """Отримує IP клієнта"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Існуючі методи залишаються без змін
def get_chat_history(request, session_id):
    """Отримати історію чату"""
    try:
        chat_session = get_object_or_404(ChatSession, id=session_id)
        messages = chat_session.messages.all().order_by('created_at')
        
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': str(message.id),
                'role': message.role,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'processing_time': message.processing_time
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def rate_chat(request):
    """Оцінити якість чату"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        rating = data.get('rating')
        feedback = data.get('feedback', '')
        
        if not session_id or not rating:
            return JsonResponse({
                'success': False,
                'error': 'Session ID та рейтинг обов\'язкові'
            }, status=400)
        
        chat_session = get_object_or_404(ChatSession, id=session_id)
        analytics, _ = ChatAnalytics.objects.get_or_create(chat_session=chat_session)
        
        analytics.satisfaction_rating = rating
        analytics.feedback = feedback
        analytics.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Дякую за оцінку!'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def consultant_stats(request):
    """Статистика консультанта (для адміністратора)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Доступ заборонено'}, status=403)
    
    total_sessions = ChatSession.objects.count()
    active_sessions = ChatSession.objects.filter(is_active=True).count()
    total_messages = Message.objects.count()
    
    # Статистика за останні 30 днів
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_sessions = ChatSession.objects.filter(created_at__gte=thirty_days_ago).count()
    recent_messages = Message.objects.filter(created_at__gte=thirty_days_ago).count()
    
    return JsonResponse({
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'total_messages': total_messages,
        'recent_sessions_30d': recent_sessions,
        'recent_messages_30d': recent_messages,
    })