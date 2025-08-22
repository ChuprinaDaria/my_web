from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.conf import settings
import json

from .models import Contact, ContactSubmission

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
        
        # Створюємо запис
        submission = ContactSubmission.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            subject=data.get('subject'),
            message=data.get('message'),
            referred_from=data.get('referred_from', 'contact_page'),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Відправляємо email адміну
        try:
            send_notification_email(submission)
        except Exception as e:
            # Логуємо помилку, але не падаємо
            print(f"Email notification failed: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Ваше повідомлення надіслано. Ми зв\'яжемося з вами найближчим часом.'
        })
        
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