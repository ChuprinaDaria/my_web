from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Employee, Contract, WorkLog
from .utils import generate_contract_pdf, generate_timesheet_pdf
import logging
import traceback

logger = logging.getLogger('hr')


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 0
    fields = ('position', 'contract_type', 'start_date', 'salary_netto', 'salary_brutto')
    readonly_fields = ('generated_at',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'phone',
        'contracts_count',
        'created_at'
    )
    
    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('created_at',)
    
    inlines = [ContractInline]
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Персональні дані (зашифровано)', {
            'fields': ('pesel', 'birth_date', 'address'),
            'classes': ('collapse',)
        }),
    )
    
    def contracts_count(self, obj):
        count = obj.contracts.count()
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">{}</span>',
            count
        )
    contracts_count.short_description = '📄 Договорів'


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    @admin.display(description='Зарплата (₴)')
    def salary_display(self, obj):
        try:
            total = obj.calculate_total_salary()
            if total is None:
                return "—"
            return f"{total:.2f} ₴"
        except Exception as e:
            return f"— ({e})"

    def status_badge(self, obj):
        if obj.pdf_file:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">✅ Згенеровано</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 10px;">❌ Не згенеровано</span>'
        )
    status_badge.short_description = 'Статус'

    def actions_column(self, obj):
        """Стовпець з кнопками дій"""
        try:
            buttons = []

            # Кнопка договору
            if not obj.pdf_file:
                url = reverse('admin:hr_contract_generate', args=[obj.pk])
                buttons.append(format_html('<a class="button" href="{}">📄 Договір</a>', url))
            else:
                try:
                    # Перевіряємо чи файл існує перед отриманням URL
                    pdf_url = obj.pdf_file.url
                    buttons.append(format_html('<a class="button" href="{}" target="_blank">📥 Договір</a>', pdf_url))
                except (ValueError, FileNotFoundError, AttributeError) as e:
                    # Якщо файл не існує або є проблема з доступом, показуємо кнопку регенерації
                    logger.warning(f"PDF file exists in DB but not accessible for contract {obj.pk}: {str(e)}")
                    url = reverse('admin:hr_contract_generate', args=[obj.pk])
                    buttons.append(format_html('<a class="button" href="{}" style="background: #ffc107;">⚠️ Регенерувати</a>', url))

            # Кнопка табелю
            timesheet_url = reverse('admin:hr_contract_timesheet', args=[obj.pk])
            if obj.timesheet_pdf:
                try:
                    # Перевіряємо чи файл існує перед отриманням URL
                    timesheet_pdf_url = obj.timesheet_pdf.url
                    buttons.append(format_html('<a class="button" href="{}" target="_blank">📊 Табель</a>', timesheet_pdf_url))
                except (ValueError, FileNotFoundError, AttributeError) as e:
                    # Якщо файл не існує, показуємо кнопку регенерації
                    logger.warning(f"Timesheet PDF file exists in DB but not accessible for contract {obj.pk}: {str(e)}")
                    buttons.append(format_html('<a class="button" href="{}" style="background: #ffc107;">⚠️ Табель</a>', timesheet_url))
            else:
                buttons.append(format_html('<a class="button" href="{}">📊 Генерувати табель</a>', timesheet_url))

            return format_html(' | '.join(buttons))
        except Exception as e:
            logger.error(f"Error in actions_column for contract {obj.pk}: {str(e)}", exc_info=True)
            return format_html('<span style="color: red;">Помилка</span>')
    actions_column.short_description = 'Дії'

    list_display = (
        'employee',
        'position',
        'contract_type',
        'start_date',
        'salary_display',
        'status_badge',
        'actions_column'
    )

    list_filter = ('contract_type', 'start_date')
    search_fields = ('employee__full_name', 'position')

    readonly_fields = ('generated_at', 'pdf_file', 'timesheet_pdf')

    fieldsets = (
        ('Працівник', {
            'fields': ('employee',)
        }),
        ('Умови праці', {
            'fields': ('position', 'contract_type', 'start_date', 'weekly_hours')
        }),
        ('Зарплата', {
            'fields': ('hourly_rate_brutto', 'salary_netto', 'salary_brutto')
        }),
        ('Договір', {
            'fields': ('generated_at', 'pdf_file'),
            'classes': ('collapse',)
        }),
        ('Табель робочого часу', {
            'fields': ('timesheet_pdf',),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:contract_id>/generate/',
                self.admin_site.admin_view(self.generate_contract_view),
                name='hr_contract_generate',
            ),
            path(
                '<int:contract_id>/generate-timesheet/',
                self.admin_site.admin_view(self.generate_timesheet_view),
                name='hr_contract_timesheet',
            ),
        ]
        return custom_urls + urls
    
    def generate_contract_view(self, request, contract_id):
        """View для генерації договору"""
        from django.shortcuts import get_object_or_404
        import traceback
        
        contract = get_object_or_404(Contract, id=contract_id)
        
        try:
            logger.info(f"Starting contract PDF generation for contract {contract_id}, employee: {contract.employee.full_name}")
            
            # Перевірка наявності CompanyInfo перед генерацією
            from contacts.models import CompanyInfo
            company = CompanyInfo.objects.filter(is_active=True).first()
            if not company:
                error_msg = "Дані компанії не налаштовані! Перевірте CompanyInfo в адмін панелі (contacts)."
                logger.error(f"CompanyInfo not found for contract {contract_id}")
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse('admin:hr_contract_change', args=[contract_id]))
            
            generate_contract_pdf(contract)
            
            # Відправка на email (додамо далі)
            # send_contract_email(contract)
            
            messages.success(request, f"Договір для {contract.employee.full_name} згенеровано успішно!")
        except ValueError as e:
            error_msg = f"Помилка налаштувань: {str(e)}"
            logger.error(f"ValueError during PDF generation for contract {contract_id}: {error_msg}", exc_info=True)
            messages.error(request, error_msg)
        except NotImplementedError as e:
            error_msg = f"Функція тимчасово недоступна: {str(e)}"
            logger.warning(f"NotImplementedError during PDF generation for contract {contract_id}: {error_msg}")
            messages.warning(request, error_msg)
        except Exception as e:
            error_msg = f"Помилка генерації: {str(e)}"
            logger.error(f"Exception during PDF generation for contract {contract_id}: {traceback.format_exc()}", exc_info=True)
            messages.error(request, f"Помилка: {str(e)}")
        
        return HttpResponseRedirect(reverse('admin:hr_contract_change', args=[contract_id]))
    
    def generate_timesheet_view(self, request, contract_id):
        """View для генерації табелю"""
        from django.shortcuts import get_object_or_404
        import traceback
        
        contract = get_object_or_404(Contract, id=contract_id)
        
        try:
            logger.info(f"Starting timesheet PDF generation for contract {contract_id}, employee: {contract.employee.full_name}")
            
            # Перевірка наявності CompanyInfo перед генерацією
            from contacts.models import CompanyInfo
            company = CompanyInfo.objects.filter(is_active=True).first()
            if not company:
                error_msg = "Дані компанії не налаштовані! Перевірте CompanyInfo в адмін панелі (contacts)."
                logger.error(f"CompanyInfo not found for timesheet generation contract {contract_id}")
                messages.error(request, error_msg)
                return HttpResponseRedirect(reverse('admin:hr_contract_change', args=[contract_id]))
            
            generate_timesheet_pdf(contract)
            messages.success(request, f"Табель для {contract.employee.full_name} згенеровано!")
        except ValueError as e:
            error_msg = f"Помилка налаштувань: {str(e)}"
            logger.error(f"ValueError during timesheet generation for contract {contract_id}: {error_msg}", exc_info=True)
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"Помилка генерації табелю: {str(e)}"
            logger.error(f"Exception during timesheet generation for contract {contract_id}: {traceback.format_exc()}", exc_info=True)
            messages.error(request, error_msg)
        
        return HttpResponseRedirect(reverse('admin:hr_contract_change', args=[contract_id]))
    


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'hours_worked', 'comment')
    list_filter = ('date', 'employee')
    search_fields = ('employee__full_name',)
    date_hierarchy = 'date'
