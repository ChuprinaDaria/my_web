import os
import requests
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class AsanaService:
    """Сервіс для роботи з Asana API"""
    
    def __init__(self):
        self.token = settings.ASANA_TOKEN or os.getenv('ASANA_TOKEN')
        self.workspace_id = settings.ASANA_WORKSPACE_ID or os.getenv('ASANA_WORKSPACE_ID')
        self.project_id = settings.ASANA_PROJECT_ID or os.getenv('ASANA_PROJECT_ID')
        
        if not all([self.token, self.workspace_id, self.project_id]):
            logger.error("Asana credentials not configured properly")
            raise ValueError("Missing Asana credentials in settings")
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }
        self.base_url = 'https://app.asana.com/api/1.0'
    
    def create_lead_task(self, submission) -> Optional[str]:
        """
        Створює таск в Asana для нового лида
        
        Args:
            submission: ContactSubmission instance
            
        Returns:
            str: Asana task ID або None якщо помилка
        """
        try:
            # Формуємо назву таска
            task_name = f"Нова заявка: {submission.name} - {submission.subject}"
            
            # Формуємо детальний опис з усіма даними
            task_description = self._build_task_description(submission)
            
            # Дані для створення таска
            task_data = {
                "data": {
                    "name": task_name,
                    "notes": task_description,
                    "projects": [self.project_id],
                    "workspace": self.workspace_id,
                    # Додаємо дедлайн - 7 днів на відповідь
                    "due_on": (submission.created_at.date() + 
                              __import__('datetime').timedelta(days=7)).isoformat(),
                    # Додаємо пріоритет
                    "priority": self._get_priority_based_on_company(submission.company),
                    # "tags": self._get_tags_for_submission(submission)  # Видаляємо цю лінію
                }
            }
            
            # Відправляємо запит до Asana API
            response = requests.post(
                f'{self.base_url}/tasks',
                headers=self.headers,
                json=task_data,
                timeout=10
            )
            
            if response.status_code == 201:
                task_id = response.json()['data']['gid']
                logger.info(f"Asana task created successfully: {task_id}")
                return task_id
            else:
                logger.error(f"Asana API error: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error creating Asana task: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating Asana task: {e}")
            return None

    def create_quote_task(self, quote_request) -> Optional[str]:
        try:
            task_name = f"Запит прорахунку: {getattr(quote_request, 'client_name', 'Клієнт')}"
            details = []
            details.append(f"• Ім'я: {getattr(quote_request, 'client_name', '')}")
            details.append(f"• Email: {getattr(quote_request, 'client_email', '')}")
            details.append(f"• Телефон: {getattr(quote_request, 'client_phone', '')}")
            details.append(f"• Компанія: {getattr(quote_request, 'client_company', '')}")
            details.append("")
            details.append("📝 Запит:")
            details.append(getattr(quote_request, 'original_query', ''))
            details.append("")
            details.append("📊 Мета-дані:")
            details.append(f"• Session ID: {getattr(quote_request, 'session_id', '')}")
            details.append(f"• IP: {getattr(quote_request, 'ip_address', '')}")
            details.append(f"• User Agent: {getattr(quote_request, 'user_agent', '')[:200]}")
            task_description = "\n".join(details)

            task_data = {
                "data": {
                    "name": task_name,
                    "notes": task_description,
                    "projects": [self.project_id],
                    "workspace": self.workspace_id,
                    "due_on": (__import__('datetime').date.today() + __import__('datetime').timedelta(days=3)).isoformat(),
                }
            }

            response = requests.post(
                f'{self.base_url}/tasks',
                headers=self.headers,
                json=task_data,
                timeout=10
            )

            if response.status_code == 201:
                return response.json()['data']['gid']
            else:
                logger.error(f"Asana API error (quote): {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating Asana quote task: {e}")
            return None

    def create_generic_task(self, name: str, notes: str, due_days: int = 3) -> Optional[str]:
        try:
            task_data = {
                "data": {
                    "name": name,
                    "notes": notes,
                    "projects": [self.project_id],
                    "workspace": self.workspace_id,
                    "due_on": (__import__('datetime').date.today() + __import__('datetime').timedelta(days=due_days)).isoformat(),
                }
            }
            response = requests.post(
                f"{self.base_url}/tasks",
                headers=self.headers,
                json=task_data,
                timeout=10
            )
            if response.status_code == 201:
                return response.json()['data']['gid']
            logger.error(f"Asana API error (generic): {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating generic Asana task: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Оновлює статус таска в Asana
        
        Args:
            task_id: ID таска в Asana
            status: Новий статус (new, contacted, qualified, etc.)
            
        Returns:
            bool: True якщо успішно оновлено
        """
        try:
            # Мапимо Django статуси на Asana
            status_mapping = {
                'new': ' Новий лід',
                'contacted': '📞 Зв\'язались',
                'qualified': '✅ Кваліфікований',
                'proposal_sent': '📋 Відправлено пропозицію',
                'negotiation': '💬 Переговори',
                'closed_won': '🎉 Закрито успішно',
                'closed_lost': '❌ Закрито неуспішно',
            }
            
            asana_status = status_mapping.get(status, status)
            
            # Оновлюємо назву таска з новим статусом
            update_data = {
                "data": {
                    "name": f"[{asana_status}] {self._get_original_task_name(task_id)}"
                }
            }
            
            response = requests.put(
                f'{self.base_url}/tasks/{task_id}',
                headers=self.headers,
                json=update_data,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error updating Asana task status: {e}")
            return False
    
    def add_task_comment(self, task_id: str, comment: str) -> bool:
        """Додає коментар до таска"""
        try:
            comment_data = {
                "data": {
                    "text": comment,
                    "target": task_id
                }
            }
            
            response = requests.post(
                f'{self.base_url}/stories',
                headers=self.headers,
                json=comment_data,
                timeout=10
            )
            
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"Error adding Asana comment: {e}")
            return False
    
    def _build_task_description(self, submission) -> str:
        """Формує детальний опис таска з усіма даними"""
        
        # Базова інформація про клієнта
        description = f"""
📧 КОНТАКТНІ ДАНІ:
• Ім'я: {submission.name}
• Email: {submission.email}
• Телефон: {submission.phone or 'Не вказано'}
• Компанія: {submission.company or 'Не вказано'}

📝 ЗАПИТ:
• Тема: {submission.subject}
• Повідомлення:
{submission.message}

🎯 CTA ТРЕКІНГ:
• CTA джерело: {submission.cta_source or 'Не вказано'}
• Сторінка: {submission.page_url or 'Не вказано'}
• Session ID: {submission.session_id or 'Не вказано'}

📊 МЕТА-ДАНІ:
• Джерело: {submission.referred_from or 'contact_page'}
• Дата створення: {submission.created_at.strftime('%d.%m.%Y о %H:%M')}
• IP адреса: {submission.ip_address or 'Невідома'}
• User Agent: {submission.user_agent[:100] + '...' if submission.user_agent and len(submission.user_agent) > 100 else submission.user_agent or 'Невідомо'}

🎯 ШВИДКІ ДІЇ:
□ Зателефонувати клієнту
□ Відправити welcome email
□ Створити пропозицію
□ Запланувати зустріч
""".encode('utf-8').decode('utf-8')
        
        return description.strip()
    
    def _get_priority_based_on_company(self, company: Optional[str]) -> str:
        """Визначає пріоритет на основі компанії"""
        if not company:
            return "medium"
        
        # Якщо компанія велика або відома - високий пріоритет
        big_companies = ['google', 'microsoft', 'apple', 'amazon', 'facebook', 'meta']
        if any(big_comp in company.lower() for big_comp in big_companies):
            return "high"
        
        return "medium"
    
    def _get_tags_for_submission(self, submission) -> list:
        """Генерує теги на основі заявки"""
        tags = []
        
        # Видаляємо автоматичні теги - вони не існують в Асані
        # if submission.referred_from:
        #     tags.append(f"source_{submission.referred_from}")
        
        # Тільки теги на основі теми (якщо вони існують в Асані)
        subject_lower = submission.subject.lower()
        if any(word in subject_lower for word in ['ai', 'штучний інтелект', 'автоматизація']):
            # tags.append("ai_services")  # Коментуємо поки не створиш тег в Асані
            pass
        elif any(word in subject_lower for word in ['сайт', 'website', 'розробка']):
            # tags.append("web_development")  # Коментуємо поки не створиш тег в Асані
            pass
        
        return []  # Повертаємо пустий список поки що
    
    def _get_original_task_name(self, task_id: str) -> str:
        """Отримує оригінальну назву таска без статусу"""
        try:
            response = requests.get(
                f'{self.base_url}/tasks/{task_id}',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                current_name = response.json()['data']['name']
                # Видаляємо статус якщо він є
                if current_name.startswith('[') and ']' in current_name:
                    return current_name.split('] ', 1)[1]
                return current_name
            
        except Exception as e:
            logger.error(f"Error getting task name: {e}")
        
        return "Заявка з сайту"  # Fallback


# Замість старого singleton
try:
    asana_service = AsanaService()
except Exception as e:
    asana_service = None
    logger.warning(f"⚠️ Asana service not initialized: {e}")
