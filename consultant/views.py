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
import random
from .models import ChatSession, Message, ConsultantProfile, KnowledgeBase, ChatAnalytics


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
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Відправити повідомлення консультанту"""
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
        
        # Оновлюємо аналітику
        analytics, _ = ChatAnalytics.objects.get_or_create(chat_session=chat_session)
        analytics.user_messages += 1
        analytics.total_messages += 1
        analytics.save()
        
        # Генеруємо відповідь консультанта
        start_time = time.time()
        assistant_response = generate_consultant_response(message_content, chat_session)
        processing_time = time.time() - start_time
        
        # Зберігаємо відповідь консультанта
        assistant_message = Message.objects.create(
            chat_session=chat_session,
            role='assistant',
            content=assistant_response,
            is_processed=True,
            processing_time=processing_time,
            tokens_used=len(assistant_response.split())  # Приблизна кількість токенів
        )
        
        # Оновлюємо аналітику
        analytics.assistant_messages += 1
        analytics.total_messages += 1
        analytics.total_tokens_used += assistant_message.tokens_used or 0
        analytics.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': str(assistant_message.id),
                'role': assistant_message.role,
                'content': assistant_message.content,
                'created_at': assistant_message.created_at.isoformat(),
                'processing_time': processing_time
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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


def generate_consultant_response(user_message, chat_session):
    """Генерує відповідь консультанта (заглушка для RAG)"""
    consultant = ConsultantProfile.objects.filter(is_active=True).first()
    
    # Простий RAG-подібний алгоритм
    knowledge_items = KnowledgeBase.objects.filter(is_active=True).order_by('-priority')
    
    # Пошук релевантних знань
    relevant_knowledge = []
    user_words = user_message.lower().split()
    
    for item in knowledge_items:
        item_words = (item.title + ' ' + item.content).lower().split()
        if any(word in item_words for word in user_words):
            relevant_knowledge.append(item)
    
    # Базові відповіді
    responses = [
        f"Дякую за ваше питання! {user_message} - це цікава тема.",
        "Я розумію ваш запит. Дозвольте мені допомогти вам з цим.",
        "Це важливе питання. Ось що я можу вам запропонувати:",
        "Відмінно! Давайте розглянемо це детальніше.",
    ]
    
    # Формуємо відповідь
    response = random.choice(responses)
    
    if relevant_knowledge:
        response += f"\n\nЗгідно з моєю базою знань:\n"
        for item in relevant_knowledge[:2]:  # Максимум 2 релевантні статті
            response += f"• {item.title}: {item.content[:200]}...\n"
    
    # Додаємо загальні поради
    general_advice = [
        "Якщо у вас є додаткові питання, не соромтеся запитати!",
        "Можу допомогти з більш детальним поясненням.",
        "Чи є щось конкретне, що вас цікавить?",
        "Готовий продовжити нашу розмову!",
    ]
    
    response += f"\n\n{random.choice(general_advice)}"
    
    return response


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