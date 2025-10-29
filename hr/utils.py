# hr/utils.py

from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime
from calendar import monthrange
import locale
import os


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
    from datetime import timedelta
    end_date = contract.start_date + timedelta(days=30)
    
    # Підготовка шляхів для зображень з перевіркою наявності файлів (WeasyPrint потребує абсолютних шляхів)
    logo_path = None
    signature_path = None
    
    try:
        if company.logo and hasattr(company.logo, 'path'):
            logo_path = company.logo.path  # Абсолютний шлях до файлу
            if not os.path.exists(logo_path):
                logo_path = None  # Файл не існує
    except (AttributeError, ValueError, Exception):
        logo_path = None
    
    try:
        if company.signature and hasattr(company.signature, 'path'):
            signature_path = company.signature.path  # Абсолютний шлях до підпису
            if not os.path.exists(signature_path):
                signature_path = None  # Файл не існує
    except (AttributeError, ValueError, Exception):
        signature_path = None
    
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
    except Exception as e:
        raise ValueError(f"Помилка рендерингу шаблону: {str(e)}")
    
    # Генеруємо PDF (використовуємо простий підхід без base_url через проблеми з WeasyPrint 61.2)
    # Зображення передаються через абсолютні шляхи у шаблоні (file://)
    try:
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()
    except Exception as e:
        raise ValueError(f"Помилка генерації PDF (WeasyPrint): {str(e)}")
    
    # Зберігаємо PDF та оновлюємо контракт (разом з розрахованою ставкою якщо була)
    filename = f"zlecenie_{contract.employee.full_name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}.pdf"
    contract.pdf_file.save(filename, ContentFile(pdf_file), save=False)
    contract.generated_at = timezone.now()
    contract.save()  # Зберігаємо контракт разом з розрахованою ставкою та інформацією про PDF
    
    return contract.pdf_file.path


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

