from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
import json
import logging
from datetime import datetime

from .models import Contact, ContactSubmission
from services.asana_service import asana_service
from news.services.telegram import tg_send_message

logger = logging.getLogger(__name__)

class ContactView(TemplateView):
    template_name = 'contacts/contacts.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Отримуємо активну контактну інформацію
        contact_info = Contact.objects.filter(is_active=True).first()
        if not contact_info:
            # Створюємо дефолтну, якщо немає
            contact_info = Contact.objects.create()
        
        context.update({
            'contact_info': contact_info,
            'page_title': contact_info.title_uk,  # Або згідно поточної мови
            'seo_title': contact_info.seo_title_uk or contact_info.title_uk,
            'seo_description': contact_info.seo_description_uk,
            # Breadcrumbs для schema.org
            'breadcrumbs': [
                {
                    'name': 'Contact' if self.request.LANGUAGE_CODE == 'en' else ('Контакти' if self.request.LANGUAGE_CODE == 'uk' else 'Kontakt'),
                    'url': self.request.path
                }
            ]
        })
        
        return context

@require_POST
@csrf_exempt  # Тимчасово, потім додаси CSRF token в форму
def submit_contact_form(request):
    """API endpoint для форми зв'язку"""
    
    try:
        # Отримуємо дані з форми
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        # Валідація обов'язкових полів
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'Поле "{field}" є обов\'язковим'
                }, status=400)
        
        # Отримуємо дані трекінгу CTA
        cta_source = data.get('cta_source', '')
        page_url = data.get('page_url', '') or request.META.get('HTTP_REFERER', '')
        session_id = data.get('session_id', '') or request.session.session_key or ''
        
        # 🔒 ДОДАЙ ЦІ ПЕРЕВІРКИ ПІСЛЯ ВАЛІДАЦІЇ ПОЛІВ, ПЕРЕД ContactSubmission.objects.create()

        # 1. Honeypot перевірка (якщо бот заповнив приховане поле)
        honeypot = data.get('website', '')  # боти заповнять це поле
        if honeypot:
            logger.warning(f"🤖 Bot detected via honeypot from {get_client_ip(request)}")
            return JsonResponse({'success': False, 'error': 'Spam detected'}, status=400)

        # 2. Rate limiting - не більше 3 заявок з однієї IP за 10 хвилин
        ip = get_client_ip(request)
        cache_key = f'contact_form_{ip}'
        submissions_count = cache.get(cache_key, 0)
        if submissions_count >= 3:
            logger.warning(f"🚫 Rate limit exceeded for {ip}")
            return JsonResponse({'success': False, 'error': 'Too many requests'}, status=429)

        # 3. Перевірка на спам-текст у темі та повідомленні
        spam_keywords = ['sex', 'casino', 'viagra', 'loan', 'depraved', 'dating']
        subject_lower = data.get('subject', '').lower()
        message_lower = data.get('message', '').lower()
        if any(keyword in subject_lower or keyword in message_lower for keyword in spam_keywords):
            logger.warning(f"🗑️ Spam content detected from {ip}")
            return JsonResponse({'success': False, 'error': 'Invalid content'}, status=400)

        # 4. Збільшуємо лічильник запитів (після всіх перевірок, перед створенням submission)
        cache.set(cache_key, submissions_count + 1, 600)  # 600 сек = 10 хвилин
        
        # Створюємо запис в БД
        submission = ContactSubmission.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            subject=data.get('subject'),
            message=data.get('message'),
            referred_from=data.get('referred_from', 'contact_page'),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            # CTA трекінг поля
            cta_source=cta_source,
            page_url=page_url,
            session_id=session_id
        )
        
        # Відправляємо відповідь користувачу НЕГАЙНО
        response = JsonResponse({
            'success': True,
            'message': 'Дякуємо! Ваше повідомлення надіслано. Ми зв\'яжемося з вами найближчим часом.'
        })
        
        # Запускаємо асинхронні завдання в фоновому режимі
        import threading
        
        def background_tasks():
            # 🚀 Створюємо таск в Asana
            try:
                if asana_service:
                    asana_task_id = asana_service.create_lead_task(submission)
                    if asana_task_id:
                        submission.asana_task_id = asana_task_id
                        submission.save(update_fields=['asana_task_id'])
                        logger.info(f"✅ Asana task created: {asana_task_id}")
                    else:
                        logger.warning("⚠️ Failed to create Asana task, but submission saved")
                else:
                    logger.warning("⚠️ Asana service not configured - check ASANA_TOKEN, ASANA_WORKSPACE_ID, ASANA_PROJECT_ID")
            except Exception as e:
                logger.error(f"⚠️ Asana integration error: {e}")
            
            # 📱 Відправляємо повідомлення в Telegram
            try:
                send_lead_notification_to_telegram(submission)
            except Exception as e:
                logger.error(f"Telegram notification failed: {e}")
            
            # Відправляємо email адміну
            try:
                send_notification_email(submission)
            except Exception as e:
                logger.error(f"Email notification failed: {e}")
        
        # Запускаємо в окремому потоці
        thread = threading.Thread(target=background_tasks)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Виникла помилка. Спробуйте ще раз або напишіть нам на info@lazysoft.pl'
        }, status=500)

def get_client_ip(request):
    """Отримуємо IP клієнта"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def send_notification_email(submission):
    """Відправляємо notification email"""
    subject = f"Нове повідомлення з сайту: {submission.subject}"
    
    message = f"""
Нове повідомлення з контактної форми:

Ім'я: {submission.name}
Email: {submission.email}
Телефон: {submission.phone or 'Не вказано'}
Компанія: {submission.company or 'Не вказано'}
Тема: {submission.subject}

Повідомлення:
{submission.message}

---
Джерело: {submission.referred_from or 'contact_page'}
IP: {submission.ip_address}
Дата: {submission.created_at}
"""
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['info@lazysoft.pl'],
        fail_silently=False,
    )

def sync_submission_to_asana(submission):
    """
    Синхронізує зміни ContactSubmission з Asana
    Використовується в admin.py або signals
    """
    if not asana_service or not submission.asana_task_id:
        return False
    
    try:
        # Оновлюємо статус в Asana
        success = asana_service.update_task_status(
            submission.asana_task_id, 
            submission.status
        )
        
        # Додаємо коментар якщо є admin_notes
        if submission.admin_notes and success:
            asana_service.add_task_comment(
                submission.asana_task_id,
                f"💬 Адмін нотатка: {submission.admin_notes}"
            )
        
        return success
        
    except Exception as e:
        print(f"Error syncing to Asana: {e}")
        return False

def send_lead_notification_to_telegram(submission):
    """
    Відправляє повідомлення про новий лід в Telegram чат з адміном
    """
    try:
        # Формуємо повідомлення
        asana_link = f"https://app.asana.com/0/0/{submission.asana_task_id}" if submission.asana_task_id else "Не створено"
        
        message = f"""
🎯 <b>НОВИЙ ЛІД З САЙТУ</b>

👤 <b>Клієнт:</b> {submission.name}
📧 <b>Email:</b> {submission.email}
📞 <b>Телефон:</b> {submission.phone or 'Не вказано'}
🏢 <b>Компанія:</b> {submission.company or 'Не вказано'}

📝 <b>Тема:</b> {submission.subject}
💬 <b>Повідомлення:</b>
{submission.message[:200]}{'...' if len(submission.message) > 200 else ''}

🎯 <b>CTA трекінг:</b>
• CTA джерело: {submission.cta_source or 'Не вказано'}
• Сторінка: {submission.page_url or 'Не вказано'}
• Session ID: {submission.session_id or 'Не вказано'}

📊 <b>Деталі:</b>
• Джерело: {submission.referred_from or 'contact_page'}
• Дата: {submission.created_at.strftime('%d.%m.%Y о %H:%M')}
• IP: {submission.ip_address or 'Невідома'}

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔗 <b>Asana таск:</b> <a href="{asana_link}">Перейти до таска</a>
        """.strip()
        
        # Відправляємо в Telegram адмінський чат
        from news.services.telegram import _tg_request
        admin_chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)
        
        if admin_chat_id:
            data = {
                "chat_id": admin_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            }
            _tg_request("sendMessage", data)
            logger.info(f"Telegram notification sent to admin chat for lead {submission.id}")
        else:
            logger.warning("No Telegram admin chat configured")
        
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")