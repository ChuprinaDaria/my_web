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
            generate_contract_pdf(contract)
            
            # Відправка на email (додамо далі)
            # send_contract_email(contract)
            
            messages.success(request, f"Договір для {contract.employee.full_name} згенеровано успішно!")
        except ValueError as e:
            error_msg = f"Помилка налаштувань: {str(e)}"
            logger.error(f"ValueError during PDF generation for contract {contract_id}: {error_msg}", exc_info=True)
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"Помилка генерації: {str(e)}"
            logger.error(f"Exception during PDF generation for contract {contract_id}: {traceback.format_exc()}")
            messages.error(request, error_msg)
        
        return HttpResponseRedirect(reverse('admin:hr_contract_change', args=[contract_id]))
    
    def generate_timesheet_view(self, request, contract_id):
        """View для генерації табелю"""
        contract = self.get_object(request, contract_id)
        
        try:
            # Можна додати вибір місяця, поки що поточний
            generate_timesheet_pdf(contract)
            messages.success(request, f"Табель для {contract.employee.full_name} згенеровано!")
        except Exception as e:
            messages.error(request, f"Помилка генерації табелю: {str(e)}")
        
        return HttpResponseRedirect(reverse('admin:hr_contract_change', args=[contract_id]))
    
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
    
    def salary_display(self, obj):
        if obj.hourly_rate_brutto:
            total = obj.calculate_total_salary()
            return format_html(
                '<strong>{:.2f} PLN/год</strong><br><small>≈ {:.2f} PLN/міс</small>',
                obj.hourly_rate_brutto,
                total
            )
        elif obj.salary_brutto:
            return f"{obj.salary_brutto} PLN/міс (brutto)"
        elif obj.salary_netto:
            return f"{obj.salary_netto} PLN/міс (netto)"
        return "-"
    salary_display.short_description = '💰 Зарплата'
    
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
        buttons = []
        
        # Кнопка договору
        if not obj.pdf_file:
            url = reverse('admin:hr_contract_generate', args=[obj.pk])
            buttons.append(format_html('<a class="button" href="{}">📄 Договір</a>', url))
        else:
            buttons.append(format_html('<a class="button" href="{}" target="_blank">📥 Договір</a>', obj.pdf_file.url))
        
        # Кнопка табелю
        timesheet_url = reverse('admin:hr_contract_timesheet', args=[obj.pk])
        if obj.timesheet_pdf:
            buttons.append(format_html('<a class="button" href="{}" target="_blank">📊 Табель</a>', obj.timesheet_pdf.url))
        else:
            buttons.append(format_html('<a class="button" href="{}">📊 Генерувати табель</a>', timesheet_url))
        
        return format_html(' | '.join(buttons))
    actions_column.short_description = 'Дії'


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'hours_worked', 'comment')
    list_filter = ('date', 'employee')
    search_fields = ('employee__full_name',)
    date_hierarchy = 'date'
