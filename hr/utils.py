# hr/utils.py

from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
import locale
import os
import logging

logger = logging.getLogger('hr')


def generate_contract_pdf(contract):
    """Генерує PDF договору для працівника"""
    from contacts.models import CompanyInfo
    
    # Автоматично розраховуємо ставку за годину якщо потрібно (без збереження)
    if not contract.hourly_rate_brutto and contract.salary_brutto and contract.weekly_hours:
        hourly_rate = contract.calculate_hourly_rate()
        if hourly_rate:
            contract.hourly_rate_brutto = hourly_rate
    
    # Отримуємо дані компанії
    company = CompanyInfo.objects.filter(is_active=True).first()
    
    if not company:
        raise ValueError("Дані компанії не налаштовані! Перевірте CompanyInfo в адмін панелі.")
    
    # Рахуємо дату закінчення (1 місяць від старту)
    end_date = contract.start_date + timedelta(days=30)
    
    # Підготовка шляхів для зображень з перевіркою наявності файлів (WeasyPrint потребує абсолютних шляхів)
    logo_path = None
    signature_path = None
    
    # Безпечний доступ до шляхів файлів (може не працювати на S3 або віддалених сховищах)
    if company.logo:
        try:
            # Перевіряємо чи є метод path (локальне сховище)
            if hasattr(company.logo, 'path'):
                try:
                    logo_path = company.logo.path
                    # Перевіряємо чи файл реально існує
                    if logo_path and os.path.exists(logo_path):
                        logo_path = logo_path
                    else:
                        logo_path = None
                        logger.warning(f"Logo file path not found: {logo_path}")
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Cannot access logo.path: {e}")
                    logo_path = None
        except Exception as e:
            logger.warning(f"Error accessing logo: {e}")
            logo_path = None
    
    if company.signature:
        try:
            # Перевіряємо чи є метод path (локальне сховище)
            if hasattr(company.signature, 'path'):
                try:
                    signature_path = company.signature.path
                    # Перевіряємо чи файл реально існує
                    if signature_path and os.path.exists(signature_path):
                        signature_path = signature_path
                    else:
                        signature_path = None
                        logger.warning(f"Signature file path not found: {signature_path}")
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Cannot access signature.path: {e}")
                    signature_path = None
        except Exception as e:
            logger.warning(f"Error accessing signature: {e}")
            signature_path = None
    
    logger.info(f"Logo path: {logo_path}, Signature path: {signature_path}")
    
    # Контекст для шаблону
    context = {
        'contract': contract,
        'employee': contract.employee,
        'company': company,
        'contract_date': contract.start_date.strftime('%d.%m.%Y'),
        'end_date': end_date.strftime('%d.%m.%Y'),
        'logo_path': logo_path,  # Додаємо абсолютний шлях для WeasyPrint
        'signature_path': signature_path,  # Додаємо абсолютний шлях до підпису
    }
    
    # Рендеримо HTML
    try:
        html_string = render_to_string('hr/zlecenie_template.html', context)
        logger.debug(f"HTML template rendered successfully, length: {len(html_string)}")
    except Exception as e:
        error_msg = f"Помилка рендерингу шаблону: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)
    
    # Генеруємо PDF (використовуємо простий підхід без base_url через проблеми з WeasyPrint 61.2)
    # Зображення передаються через абсолютні шляхи у шаблоні (file://)
    try:
        logger.debug("Starting PDF generation with WeasyPrint...")
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()
        logger.info(f"PDF generated successfully, size: {len(pdf_file)} bytes")
    except Exception as e:
        error_msg = f"Помилка генерації PDF (WeasyPrint): {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)
    
    # Зберігаємо PDF та оновлюємо контракт (разом з розрахованою ставкою якщо була)
    try:
        filename = f"zlecenie_{contract.employee.full_name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}.pdf"
        contract.pdf_file.save(filename, ContentFile(pdf_file), save=False)
        contract.generated_at = timezone.now()
        contract.save()  # Зберігаємо контракт разом з розрахованою ставкою та інформацією про PDF
        logger.info(f"PDF saved successfully: {filename}")
        
        # Повертаємо шлях або URL залежно від типу сховища
        try:
            return contract.pdf_file.path
        except (AttributeError, ValueError):
            return contract.pdf_file.url
    except Exception as e:
        error_msg = f"Помилка збереження PDF: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)


def generate_timesheet_pdf(contract, month=None, year=None):
    """Генерує заповнений табель годин для працівника"""
    from contacts.models import CompanyInfo
    
    company = CompanyInfo.objects.filter(is_active=True).first()
    
    if not company:
        raise ValueError("Дані компанії не налаштовані!")
    
    # Якщо місяць не вказаний - беремо поточний
    if not month or not year:
        now = datetime.now()
        month = now.month
        year = now.year
    
    # Кількість днів в місяці
    num_days = monthrange(year, month)[1]
    
    # Години на день (weekly_hours / 5 робочих днів)
    if contract.weekly_hours:
        hours_per_day = contract.weekly_hours / 5
    else:
        hours_per_day = 8  # За замовчуванням
    
    # Генеруємо дні з годинами
    days_data = []
    total_hours = 0
    
    try:
        locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
    except:
        pass
    
    for day in range(1, num_days + 1):
        date = datetime(year, month, day)
        weekday = date.weekday()  # 0=Monday, 6=Sunday
        
        # Робочі дні: Пн-Пт (0-4)
        if weekday < 5:
            hours = hours_per_day
            total_hours += hours
        else:
            hours = None  # Вихідний
        
        days_data.append({
            'day': day,
            'hours': f"{hours:.1f}" if hours else "",
        })
    
    # Назва місяця польською
    month_names_pl = [
        '', 'styczeń', 'luty', 'marzec', 'kwiecień', 'maj', 'czerwiec',
        'lipiec', 'sierpień', 'wrzesień', 'październik', 'listopad', 'grudzień'
    ]
    
    context = {
        'contract': contract,
        'employee': contract.employee,
        'company': company,
        'days_data': days_data,
        'total_hours': f"{total_hours:.1f}",
        'month_year': f"{month_names_pl[month]} {year}",
    }
    
    # Рендеримо HTML
    try:
        html_string = render_to_string('hr/timesheet_template.html', context)
    except Exception as e:
        raise ValueError(f"Помилка рендерингу шаблону табелю: {str(e)}")
    
    # Генеруємо PDF
    try:
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()
    except Exception as e:
        raise ValueError(f"Помилка генерації PDF табелю (WeasyPrint): {str(e)}")
    
    # Зберігаємо
    filename = f"timesheet_{contract.employee.full_name.replace(' ', '_')}_{month:02d}_{year}.pdf"
    contract.timesheet_pdf.save(filename, ContentFile(pdf_file), save=False)
    contract.save()
    
    return contract.timesheet_pdf.path

