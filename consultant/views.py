# consultant/views.py - оновлена версія з RAG
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
import uuid
import time

from .models import ChatSession, Message, ConsultantProfile, KnowledgeBase, ChatAnalytics
from .rag_integration import enhanced_consultant

# Імпортуємо pricing моделі якщо доступні
try:
    from pricing.models import QuoteRequest
    PRICING_AVAILABLE = True
except ImportError:
    PRICING_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)


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
        
        # Створюємо або отримуємо сесію
        chat_session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': request.user if request.user.is_authenticated else None,
                'user_ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
        
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
        
        # 💰 Логіка для pricing запитів
        additional_data = {}
        if rag_result['intent'] == 'pricing' and PRICING_AVAILABLE:
            additional_data['show_quote_form'] = True
            additional_data['detected_services'] = _extract_services_from_sources(rag_result.get('sources', []))
        
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
                'method': rag_result['method']
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
        
        # Визначаємо сервіс з контексту чату
        detected_service = None
        if chat_session:
            # Аналізуємо останні повідомлення для визначення сервісу
            recent_messages = chat_session.messages.filter(role='user').order_by('-created_at')[:3]
            recent_text = ' '.join([msg.content for msg in recent_messages])
            
            # Спрощена логіка визначення сервісу
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
        
        # Оновлюємо сесію чату
        if chat_session:
            analytics, _ = ChatAnalytics.objects.get_or_create(chat_session=chat_session)
            # Можна додати поле quote_requested в ChatAnalytics модель
        
        # TODO: Відправити в Celery для асинхронної обробки PDF та email
        # process_quote_request.delay(quote_request.id)
        
        return JsonResponse({
            'success': True,
            'message': 'Запит отримано! Прорахунок буде відправлений на ваш email протягом 30 хвилин.',
            'quote_id': quote_request.id
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